# renderer.py
# Generation logic for "deluxe poop" video creation.
# Uses MoviePy to compose clips; OpenCV to gather metadata where needed.
# This implementation creates randomized chop-and-splice effects,
# overlays images/gifs randomly, and mixes audio sources.

import os
import random
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
import tempfile
import shutil
import cv2

def _safe_video_clip(path, target_w=1280, target_h=720, max_duration=6):
    # create a short randomized clip from a video or GIF
    clip = VideoFileClip(path)
    duration = clip.duration
    if duration <= 0.1:
        raise RuntimeError(f"Unreadable clip: {path}")
    # pick a random start and short subclip size
    sub_dur = min(max_duration, max(0.5, duration / 4.0))
    start = random.uniform(0, max(0, duration - sub_dur))
    sub = clip.subclip(start, start + sub_dur)
    # random speed change
    if random.random() < 0.5:
        factor = random.uniform(0.5, 2.5)
        try:
            sub = sub.fx(vfx_speedx, factor)  # local wrapper to avoid missing direct import vfx
        except Exception:
            try:
                sub = sub.fx("speedx", factor)
            except Exception:
                pass
    # resize to target while keeping aspect
    sub = sub.resize(height=target_h) if sub.w < target_w else sub.resize(width=target_w)
    return sub

def vfx_speedx(clip, factor):
    # minimal speedx implementation wrapper for older/newer moviepy versions
    try:
        return clip.fx(__import__("moviepy.video.fx.all", fromlist=["speedx"]).speedx, factor)
    except Exception:
        try:
            from moviepy.video.fx import speedx
            return speedx(clip, factor)
        except Exception:
            # fallback: return clip unchanged
            return clip

def generate_deluxe_poop(sources, output_path, progress_cb=None):
    """
    sources: dict with keys 'videos', 'audios', 'images', 'gifs' -> lists of file paths
    progress_cb(percent:int, message:str)
    """
    if progress_cb:
        progress_cb(0, "Initializing...")
    tmpdir = tempfile.mkdtemp(prefix="freepoop_")
    clips = []
    try:
        total_sources = sum(len(sources.get(k, [])) for k in ['videos', 'gifs', 'images'])
        idx = 0
        # 1) create video segments from videos and gifs
        for vlist in (sources.get('videos', []), sources.get('gifs', [])):
            for path in vlist:
                idx += 1
                pct = int(20 * idx / max(1, total_sources))
                if progress_cb:
                    progress_cb(pct, f"Processing source {os.path.basename(path)}")
                try:
                    clip = _safe_video_clip(path)
                    clips.append(clip)
                except Exception as e:
                    # skip problematic clips but log via progress message
                    if progress_cb:
                        progress_cb(pct, f"Skipped {os.path.basename(path)}: {e}")
        # 2) add images as short clips
        for img in sources.get('images', []):
            idx += 1
            if progress_cb:
                progress_cb(30 + int(20 * idx / max(1, total_sources)), f"Adding image {os.path.basename(img)}")
            ic = ImageClip(img).set_duration(random.uniform(1.0, 3.0)).resize(width=720)
            # random zoom/pan not implemented; left as simple clip
            clips.append(ic)

        if not clips:
            raise RuntimeError("No usable visual sources provided (videos/gifs/images).")

        if progress_cb:
            progress_cb(60, "Applying random ordering and effects")

        # randomize and apply quick effects: alternate order, mirror some clips
        random.shuffle(clips)
        for i, c in enumerate(clips):
            if random.random() < 0.3:
                try:
                    c = c.fx(__import__("moviepy.video.fx.all", fromlist=["mirror_x"]).mirror_x)
                except Exception:
                    pass
            clips[i] = c

        # 3) concatenate
        final = concatenate_videoclips(clips, method="compose")
        # 4) optionally attach audio
        if sources.get('audios'):
            # pick a random audio or concatenate simple chain
            aud_paths = list(sources.get('audios'))
            chosen = random.choice(aud_paths)
            if progress_cb:
                progress_cb(75, f"Attaching audio {os.path.basename(chosen)}")
            try:
                audio = AudioFileClip(chosen).subclip(0, min(AudioFileClip(chosen).duration, final.duration))
                final = final.set_audio(audio)
            except Exception as e:
                if progress_cb:
                    progress_cb(75, f"Failed to attach audio: {e}")

        # 5) write output
        if progress_cb:
            progress_cb(80, "Rendering final video (this may take a while)...")
        # moviepy parameters; older versions might require different args — we use common ones
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, preset="medium", verbose=False, progress_bar=False)
        if progress_cb:
            progress_cb(100, "Render complete")
    finally:
        # cleanup
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass