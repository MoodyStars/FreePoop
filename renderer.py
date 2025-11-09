# renderer.py
# Generation logic for "deluxe poop" video creation.
# Uses MoviePy to compose clips; avoids requiring OpenCV at import time so
# the module can be imported even when opencv-python (cv2) isn't installed.
# Robust write_videofile handling: try several kwargs sets to remain compatible
# with different MoviePy versions (some versions don't accept 'progress_bar').

import os
import random
import tempfile
import shutil

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
)

def _import_vfx():
    """
    Try to import common vfx functions in a resilient way.
    Returns a dict with possible functions (speedx, mirror_x) or None values.
    """
    try:
        mod = __import__("moviepy.video.fx.all", fromlist=["speedx", "mirror_x"])
        return {
            "speedx": getattr(mod, "speedx", None),
            "mirror_x": getattr(mod, "mirror_x", None),
        }
    except Exception:
        try:
            from moviepy.video.fx import speedx as _speedx  # type: ignore
            from moviepy.video.fx import mirror_x as _mirror_x  # type: ignore
            return {"speedx": _speedx, "mirror_x": _mirror_x}
        except Exception:
            return {"speedx": None, "mirror_x": None}

_VFX = _import_vfx()

def vfx_speedx(clip, factor):
    """Apply speedx if available; otherwise return original clip."""
    speedx_fn = _VFX.get("speedx") if _VFX else None
    if speedx_fn:
        try:
            return clip.fx(speedx_fn, factor)
        except Exception:
            try:
                return clip.fx("speedx", factor)
            except Exception:
                return clip
    else:
        return clip

def _safe_video_clip(path, target_w=1280, target_h=720, max_duration=6):
    """
    Create a short randomized clip from a video or GIF using MoviePy only.
    Raises RuntimeError on unreadable clips.
    """
    clip = VideoFileClip(path)
    duration = clip.duration or 0.0
    if duration <= 0.05:
        clip.close()
        raise RuntimeError(f"Unreadable clip: {path}")

    # pick subclip duration and start
    sub_dur = min(max_duration, max(0.5, duration / 4.0))
    start = random.uniform(0, max(0, duration - sub_dur))
    sub = clip.subclip(start, start + sub_dur)

    # random speed change
    if random.random() < 0.5:
        factor = random.uniform(0.5, 2.5)
        try:
            sub = vfx_speedx(sub, factor)
        except Exception:
            pass

    # resize to target while keeping aspect ratio
    try:
        if getattr(sub, "w", 0) < target_w:
            sub = sub.resize(height=target_h)
        else:
            sub = sub.resize(width=target_w)
    except Exception:
        pass

    # Note: do not close 'clip' because sub references frames from it.
    return sub

def _try_write_videofile(final_clip, output_path, progress_cb=None):
    """
    Try writing the clip using several candidate kwargs sets to be compatible
    with multiple MoviePy versions (some don't accept 'progress_bar', 'threads', 'preset', etc).
    Calls progress_cb at start/end if provided.
    """
    # Candidate kwarg sets in preferred -> fallback order
    candidate_kw_sets = [
        {"codec": "libx264", "audio_codec": "aac", "threads": 4, "preset": "medium", "verbose": False},
        {"codec": "libx264", "audio_codec": "aac", "verbose": False},
        {"codec": "libx264", "audio_codec": "aac"},
        {"codec": "libx264", "verbose": False},
        {"verbose": False},
        {}
    ]

    last_exc = None
    for kw in candidate_kw_sets:
        try:
            if progress_cb:
                progress_cb(85, f"Writing with kwargs: {', '.join(sorted(kw.keys())) or 'none'}")
            final_clip.write_videofile(output_path, **kw)
            return
        except TypeError as e:
            # likely unsupported kw arg(s) -> try next candidate
            last_exc = e
            continue
        except Exception as e:
            # other errors should surface (disk full, ffmpeg missing, codec issues). re-raise.
            raise

    # if we exhausted candidates and only got TypeError(s), raise a clear error
    raise TypeError(f"write_videofile failed with incompatible arguments. Last error: {last_exc}")

def generate_deluxe_poop(sources, output_path, progress_cb=None):
    """
    sources: dict with keys 'videos', 'audios', 'images', 'gifs' -> lists of file paths
    progress_cb(percent:int, message:str)
    """
    if progress_cb:
        progress_cb(0, "Initializing...")
    tmpdir = tempfile.mkdtemp(prefix="freepoop_")
    clips = []
    created_clips = []
    audio_clip = None
    final = None
    try:
        visual_lists = list(sources.get('videos', [])) + list(sources.get('gifs', [])) + list(sources.get('images', []))
        total_sources = max(1, len(visual_lists))
        idx = 0

        # 1) create video / gif segments
        for path in list(sources.get('videos', [])) + list(sources.get('gifs', [])):
            idx += 1
            pct = int(20 * idx / total_sources)
            if progress_cb:
                progress_cb(pct, f"Processing source {os.path.basename(path)}")
            try:
                clip = _safe_video_clip(path)
                clips.append(clip)
                created_clips.append(clip)
            except Exception as e:
                if progress_cb:
                    progress_cb(pct, f"Skipped {os.path.basename(path)}: {e}")

        # 2) add images as short clips
        for img in sources.get('images', []):
            idx += 1
            pct = 30 + int(20 * idx / total_sources)
            if progress_cb:
                progress_cb(pct, f"Adding image {os.path.basename(img)}")
            try:
                ic = ImageClip(img).set_duration(random.uniform(1.0, 3.0))
                try:
                    ic = ic.resize(width=720)
                except Exception:
                    pass
                clips.append(ic)
                created_clips.append(ic)
            except Exception as e:
                if progress_cb:
                    progress_cb(pct, f"Skipped image {os.path.basename(img)}: {e}")

        if not clips:
            raise RuntimeError("No usable visual sources provided (videos/gifs/images).")

        if progress_cb:
            progress_cb(60, "Applying random ordering and effects")

        # randomize ordering and apply some simple effects (mirror_x if available)
        random.shuffle(clips)
        mirror_fn = _VFX.get("mirror_x") if _VFX else None
        for i, c in enumerate(clips):
            try:
                if mirror_fn and random.random() < 0.3:
                    try:
                        c = c.fx(mirror_fn)
                    except Exception:
                        try:
                            c = c.fx("mirror_x")
                        except Exception:
                            pass
                clips[i] = c
            except Exception:
                clips[i] = c

        if progress_cb:
            progress_cb(70, "Concatenating clips")

        # 3) concatenate (use compose to handle different sizes)
        final = concatenate_videoclips(clips, method="compose")

        # 4) optionally attach audio
        if sources.get('audios'):
            aud_paths = list(sources.get('audios'))
            chosen = random.choice(aud_paths)
            if progress_cb:
                progress_cb(75, f"Attaching audio {os.path.basename(chosen)}")
            try:
                audio_clip = AudioFileClip(chosen)
                if audio_clip.duration and final.duration:
                    audio_clip = audio_clip.subclip(0, min(audio_clip.duration, final.duration))
                final = final.set_audio(audio_clip)
            except Exception as e:
                if progress_cb:
                    progress_cb(75, f"Failed to attach audio: {e}")
                try:
                    if audio_clip:
                        audio_clip.close()
                except Exception:
                    pass
                audio_clip = None

        # 5) write output with robust kwarg handling
        if progress_cb:
            progress_cb(80, "Rendering final video (this may take a while)...")
        _try_write_videofile(final, output_path, progress_cb=progress_cb)

        if progress_cb:
            progress_cb(100, "Render complete")
    finally:
        # cleanup: close all clips to free resources
        try:
            if final is not None:
                try:
                    final.close()
                except Exception:
                    pass
        except Exception:
            pass
        for c in created_clips:
            try:
                c.close()
            except Exception:
                pass
        try:
            if audio_clip is not None:
                try:
                    audio_clip.close()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass