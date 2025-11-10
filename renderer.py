# renderer.py
# Generation pipeline for FreePoop 0.5 — improved write_videofile compatibility
#
# This version improves robustness when calling clip.write_videofile by:
# - Inspecting the final.write_videofile signature and only passing supported kwargs.
# - Falling back through progressively smaller kwarg sets if a TypeError occurs.
# - As a last-resort fallback, exporting frames + audio and calling ffmpeg directly.
#
# The goal is to avoid "unexpected keyword argument" errors across many MoviePy versions,
# and to surface helpful progress messages via progress_cb.

import os
import random
import tempfile
import shutil
import subprocess
import inspect
import math
from typing import Optional

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
    CompositeVideoClip,
)

# resilient vfx import helper (may be partial depending on MoviePy)
def _import_vfx():
    try:
        mod = __import__("moviepy.video.fx.all", fromlist=["speedx", "mirror_x"])
        return mod
    except Exception:
        try:
            import moviepy.video.fx as mod2  # type: ignore
            return mod2
        except Exception:
            return None

_VFX = _import_vfx()

def _v_speedx(clip, factor):
    try:
        if _VFX and hasattr(_VFX, "speedx"):
            return clip.fx(_VFX.speedx, factor)
        return clip.fx("speedx", factor)
    except Exception:
        return clip

def _v_mirror_x(clip):
    try:
        if _VFX and hasattr(_VFX, "mirror_x"):
            return clip.fx(_VFX.mirror_x)
        return clip.fx("mirror_x")
    except Exception:
        return clip

def _safe_video_clip(path, target_w=1280, target_h=720, max_duration=6):
    clip = VideoFileClip(path)
    dur = clip.duration or 0.0
    if dur <= 0.05:
        clip.close()
        raise RuntimeError("Unreadable clip: " + path)
    sub_dur = min(max_duration, max(0.5, dur / 4.0))
    start = random.uniform(0, max(0, dur - sub_dur))
    sub = clip.subclip(start, start + sub_dur)
    # random speed occasionally
    if random.random() < 0.4:
        factor = random.uniform(0.6, 2.2)
        try:
            sub = _v_speedx(sub, factor)
        except Exception:
            pass
    try:
        if getattr(sub, "w", 0) < target_w:
            sub = sub.resize(height=target_h)
        else:
            sub = sub.resize(width=target_w)
    except Exception:
        pass
    return sub

# ---------- robust write helpers ----------

def _filter_kwargs_for_callable(callable_obj, kwargs: dict) -> dict:
    """
    Inspect callable_obj's signature and return a dict containing only kwargs
    that are accepted by the callable. If inspection fails, return kwargs unmodified.
    """
    try:
        sig = inspect.signature(callable_obj)
        allowed = {}
        for k, v in kwargs.items():
            if k in sig.parameters:
                allowed[k] = v
        return allowed
    except (ValueError, TypeError):
        # can't inspect: fall back to returning the dict as-is and let caller handle TypeError
        return kwargs

def _call_write_with_filtered_kwargs(final_clip, output_path, preferred_kwargs, progress_cb=None):
    """
    Try to call final_clip.write_videofile by filtering preferred_kwargs to what the
    function signature accepts. If TypeError occurs, progressively remove optional args
    and retry. Returns normally on success or raises the last exception.
    """
    write_fn = getattr(final_clip, "write_videofile", None)
    if write_fn is None:
        raise RuntimeError("final clip does not have write_videofile method")

    # First, try to filter kwargs by signature
    kwargs = _filter_kwargs_for_callable(write_fn, preferred_kwargs)
    last_exc = None

    # Attempt a few times: if the function still rejects unknown kwargs (TypeError),
    # progressively remove keys (start with less essential ones).
    keys_order = list(kwargs.keys())
    # define removal priority: try removing larger / optional keys first
    removal_priority = ["progress_bar", "threads", "preset", "verbose", "audio_codec", "codec"]

    # Try once with the filtered kwargs
    try:
        if progress_cb:
            progress_cb(82, f"Attempting write_videofile with args: {', '.join(sorted(kwargs.keys())) or 'none'}")
        return write_fn(output_path, **kwargs)
    except TypeError as e:
        last_exc = e

    # Progressive removal loop
    remaining = dict(kwargs)
    for rem in removal_priority:
        if rem in remaining:
            del remaining[rem]
            try:
                if progress_cb:
                    progress_cb(83, f"Retrying write_videofile without '{rem}'")
                return write_fn(output_path, **remaining)
            except TypeError as e:
                last_exc = e
                continue
            except Exception as e:
                # not a TypeError -> bubble up (ffmpeg or writing error)
                raise

    # Try calling with no kwargs
    try:
        if progress_cb:
            progress_cb(84, "Retrying write_videofile with no kwargs")
        return write_fn(output_path)
    except Exception as e:
        # Keep last exception for final error reporting
        last_exc = e

    # If we reach here, we couldn't call write_videofile successfully.
    raise last_exc

def _ffmpeg_frame_export_fallback(final_clip, output_path, progress_cb=None):
    """
    Last-resort fallback: export frames to disk and use ffmpeg to assemble them
    into a video, then optionally merge audio back in.
    This is slow and disk-intensive, but works when moviepy's writer interface is incompatible.
    """
    tmpdir = tempfile.mkdtemp(prefix="freepoop_frames_")
    audio_tmp = None
    try:
        duration = final_clip.duration or 0.0
        fps = getattr(final_clip, "fps", None) or 24.0
        fps = float(fps)
        if fps <= 0:
            fps = 24.0
        total_frames = max(1, int(math.ceil(duration * fps)))
        if progress_cb:
            progress_cb(85, f"Fallback: exporting {total_frames} frames at {fps} fps to {tmpdir}")

        # export frames
        t = 0.0
        frame_idx = 0
        while frame_idx < total_frames:
            try:
                frame = final_clip.get_frame(t)  # ndarray in RGB
            except Exception as e:
                # stop early if frame extraction fails
                break
            try:
                from PIL import Image
                im = Image.fromarray(frame)
                fname = os.path.join(tmpdir, f"frame_{frame_idx:06d}.png")
                im.save(fname, format="PNG")
            except Exception as e:
                # continue but break if saving fails
                raise RuntimeError(f"Failed to save frame {frame_idx}: {e}")
            frame_idx += 1
            t += 1.0 / fps
            if progress_cb and frame_idx % max(1, int(fps)) == 0:
                pct = 85 + int(5 * frame_idx / total_frames)
                progress_cb(pct, f"Exported {frame_idx}/{total_frames} frames")

        # write audio to temporary file if present
        if getattr(final_clip, "audio", None) is not None:
            audio_tmp = os.path.join(tmpdir, "audio_temp.wav")
            try:
                if progress_cb:
                    progress_cb(90, "Exporting audio track (fallback)")
                final_clip.audio.write_audiofile(audio_tmp, verbose=False, logger=None)
            except Exception:
                # try with different signature
                try:
                    final_clip.audio.write_audiofile(audio_tmp)
                except Exception as e:
                    # audio extraction failed; ignore audio
                    audio_tmp = None

        # Build ffmpeg command to assemble frames into a video
        # The pattern must match the saved filenames frame_000000.png etc.
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(int(round(fps))),
            "-i", os.path.join(tmpdir, "frame_%06d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ]
        if audio_tmp:
            ffmpeg_cmd += ["-i", audio_tmp, "-c:a", "aac", "-shortest"]
        ffmpeg_cmd += [output_path]

        if progress_cb:
            progress_cb(95, "Running ffmpeg to assemble video (fallback)")

        proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed (fallback): {proc.returncode}\n{proc.stderr}")

        if progress_cb:
            progress_cb(99, "ffmpeg fallback complete")
        return
    finally:
        try:
            # keep tmpdir removal tolerant in case user wants to inspect files for debugging
            shutil.rmtree(tmpdir)
        except Exception:
            pass

# ---------- main generation pipeline (simplified / modular) ----------

def _try_write_final(final_clip, output_path, progress_cb=None):
    """
    High-level writer that tries signature-filtered write, then progressive fallback,
    then frame-export + ffmpeg as a last resort.
    """
    # Preferred kwargs to try
    preferred = {
        "codec": "libx264",
        "audio_codec": "aac",
        "threads": 4,
        "preset": "medium",
        "verbose": False,
        # older/newer MoviePy versions may accept progress_bar / logger; we don't include progress_bar
    }

    try:
        return _call_write_with_filtered_kwargs(final_clip, output_path, preferred, progress_cb=progress_cb)
    except TypeError as e:
        # Signature incompatibility; try a simpler candidate set (this catches unexpected kw errors)
        if progress_cb:
            progress_cb(None, f"write_videofile signature mismatch: {e}; trying simpler kwargs")
        try:
            reduced = {"codec": "libx264", "audio_codec": "aac", "verbose": False}
            reduced = _filter_kwargs_for_callable(getattr(final_clip, "write_videofile"), reduced)
            return getattr(final_clip, "write_videofile")(output_path, **reduced)
        except Exception as e2:
            # If this fails, try no-kwargs call
            if progress_cb:
                progress_cb(None, f"Simpler write attempt failed: {e2}; trying no-kwargs call")
            try:
                return getattr(final_clip, "write_videofile")(output_path)
            except Exception as e3:
                # As a last resort, run the ffmpeg frame-export fallback
                if progress_cb:
                    progress_cb(None, f"No-kwargs write failed: {e3}; using ffmpeg frame-export fallback")
                _ffmpeg_frame_export_fallback(final_clip, output_path, progress_cb=progress_cb)
                return

def _apply_basic_effects_to_clip(clip, effects):
    # A small place to add clip-wise effects; mostly placeholders for extensibility.
    try:
        if effects.get("reverse"):
            try:
                clip = clip.fx(lambda c: c.fx("time_mirror"))
            except Exception:
                try:
                    clip = clip.fx("reverse")
                except Exception:
                    pass
    except Exception:
        pass
    return clip

def make_color_frame(w, h, color=(255,0,0,80)):
    """
    Create a temporary PNG file filled by color (RGBA) and return its path.
    Used for simple tint/overlay placeholders.
    """
    from PIL import Image
    im = Image.new("RGBA", (max(1, int(w)), max(1, int(h))), color)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    im.save(tmp.name)
    tmp.close()
    return tmp.name

def generate_deluxe_poop(sources, output_path, options=None, progress_cb=None):
    """
    sources: dict with keys videos, audios, images, gifs, transitions, online
    options: dict with keys mode (deluxe/tennis/ytpmv), ai_year, effects (dict)
    progress_cb: callable(percent:int or None, message:str)
    """
    if progress_cb:
        progress_cb(0, "Initializing generation...")
    options = options or {}
    effects = options.get("effects", {}) if options else {}
    tmpdir = tempfile.mkdtemp(prefix="freepoop_")
    created_clips = []
    final = None
    audio_clip = None

    try:
        visuals = list(sources.get("videos", [])) + list(sources.get("gifs", [])) + list(sources.get("images", []))
        total = max(1, len(visuals))
        idx = 0

        clips = []
        # process videos/gifs
        for p in list(sources.get("videos", [])) + list(sources.get("gifs", [])):
            idx += 1
            if progress_cb:
                progress_cb(int(10 + 40 * idx / total), f"Processing visual {os.path.basename(p)}")
            try:
                clip = _safe_video_clip(p)
                clip = _apply_basic_effects_to_clip(clip, effects)
                clips.append(clip)
                created_clips.append(clip)
            except Exception as e:
                if progress_cb:
                    progress_cb(None, f"Skipped {os.path.basename(p)}: {e}")

        # images
        for img in sources.get("images", []):
            idx += 1
            if progress_cb:
                progress_cb(int(30 + 10 * idx / total), f"Adding image {os.path.basename(img)}")
            try:
                ic = ImageClip(img).set_duration(random.uniform(1.0, 3.0)).resize(width=720)
                clips.append(ic)
                created_clips.append(ic)
            except Exception as e:
                if progress_cb:
                    progress_cb(None, f"Skipped image {os.path.basename(img)}: {e}")

        if not clips:
            raise RuntimeError("No usable visual sources provided (videos/gifs/images).")

        if progress_cb:
            progress_cb(60, "Applying global ordering/effects")
        random.shuffle(clips)

        # insert transitions between clips if provided
        transitions = list(sources.get("transitions", []))
        if transitions and clips:
            assembled = []
            t_i = 0
            for i, c in enumerate(clips):
                assembled.append(c)
                if i < len(clips) - 1 and transitions:
                    try:
                        tr = _safe_video_clip(transitions[t_i % len(transitions)], max_duration=1.0)
                        assembled.append(tr)
                        created_clips.append(tr)
                        t_i += 1
                    except Exception:
                        pass
            clips = assembled

        if progress_cb:
            progress_cb(75, "Concatenating final composition")
        final = concatenate_videoclips(clips, method="compose")

        # overlays (simple placeholders)
        if effects.get("mlg"):
            try:
                overlay_path = make_color_frame(final.w, final.h, color=(0,255,0,60))
                overlay_clip = ImageClip(overlay_path).set_duration(min(3, final.duration)).set_pos(("center", "center"))
                final = CompositeVideoClip([final, overlay_clip])
                # cleanup overlay file later
                created_clips.append(overlay_clip)
                try:
                    os.remove(overlay_path)
                except Exception:
                    pass
            except Exception:
                pass

        # audio attachment
        audio_paths = list(sources.get("audios", []))
        if options.get("mode") == "ytpmv" and audio_paths:
            chosen = random.choice(audio_paths)
            if progress_cb:
                progress_cb(78, f"Attaching music {os.path.basename(chosen)}")
            try:
                audio_clip = AudioFileClip(chosen)
                if audio_clip.duration and final.duration:
                    audio_clip = audio_clip.subclip(0, min(audio_clip.duration, final.duration))
                final = final.set_audio(audio_clip)
            except Exception as e:
                if progress_cb:
                    progress_cb(None, f"Failed to attach audio: {e}")
                try:
                    if audio_clip:
                        audio_clip.close()
                except Exception:
                    pass
                audio_clip = None
        elif audio_paths:
            # attach random sound
            try:
                chosen = random.choice(audio_paths)
                audio_clip = AudioFileClip(chosen)
                if audio_clip.duration and final.duration:
                    audio_clip = audio_clip.subclip(0, min(audio_clip.duration, final.duration))
                final = final.set_audio(audio_clip)
            except Exception:
                audio_clip = None

        # final render
        if progress_cb:
            progress_cb(80, "Rendering final video (moviepy / ffmpeg)")
        _try_write_final(final, output_path, progress_cb=progress_cb)
        if progress_cb:
            progress_cb(100, "Render complete")
    finally:
        # cleanup
        try:
            if final is not None:
                final.close()
        except Exception:
            pass
        for c in created_clips:
            try:
                c.close()
            except Exception:
                pass
        try:
            if audio_clip is not None:
                audio_clip.close()
        except Exception:
            pass
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass