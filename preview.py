# preview.py
# Video preview utility: uses OpenCV if available, otherwise falls back to MoviePy.
# Works inside a background thread and updates a Tkinter Canvas via .after()

import threading
import time
from PIL import Image, ImageTk

# try OpenCV first
_try_cv2 = True
try:
    import cv2
except Exception:
    cv2 = None
    _try_cv2 = False

# fallback uses moviepy
_moviepy_available = True
if not _try_cv2:
    try:
        from moviepy.editor import VideoFileClip
    except Exception:
        VideoFileClip = None
        _moviepy_available = False

class VideoPreview:
    """
    VideoPreview(canvas)
    - play(path): start previewing the file at path
    - stop(): stop playback
    Uses OpenCV.VideoCapture if available; otherwise MoviePy VideoFileClip.
    """

    def __init__(self, tk_canvas):
        self.canvas = tk_canvas
        self._playing = False
        self._thread = None
        self._lock = threading.Lock()
        self._canvas_image_id = None
        self._cap = None     # for cv2 backend
        self._clip = None    # for moviepy backend

    def play(self, path):
        """
        Start playing the given path. If already playing, stops first.
        Raises RuntimeError if no backend can open the file.
        """
        with self._lock:
            self.stop()

            # Try cv2 backend
            if cv2 is not None:
                cap = cv2.VideoCapture(path)
                if cap is not None and cap.isOpened():
                    self._cap = cap
                    self._playing = True
                    self._thread = threading.Thread(target=self._play_loop_cv2, daemon=True)
                    self._thread.start()
                    return
                else:
                    try:
                        if cap:
                            cap.release()
                    except Exception:
                        pass
                    self._cap = None

            # Try moviepy backend
            if VideoFileClip is not None:
                try:
                    clip = VideoFileClip(path)
                    if clip.duration is None:
                        clip.close()
                        raise RuntimeError("Unreadable clip")
                    self._clip = clip
                    self._playing = True
                    self._thread = threading.Thread(target=self._play_loop_moviepy, daemon=True)
                    self._thread.start()
                    return
                except Exception as e:
                    try:
                        if 'clip' in locals() and clip is not None:
                            clip.close()
                    except Exception:
                        pass
                    self._clip = None
                    raise RuntimeError(f"Can't open file for preview ({path}): {e}")

            # No backend available
            raise RuntimeError("No preview backend available: install opencv-python or moviepy")

    def stop(self):
        with self._lock:
            self._playing = False
            # release cv2 capture
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
            # close moviepy clip
            if self._clip is not None:
                try:
                    self._clip.close()
                except Exception:
                    pass
                self._clip = None

    def _update_canvas_image(self, pil_img):
        """Schedule a canvas update on the Tk main thread. Keeps a reference on canvas to avoid GC."""
        tk_img = ImageTk.PhotoImage(pil_img)
        def _do():
            # store reference so Tk doesn't GC it
            self.canvas.image_ref = tk_img
            c_w = int(self.canvas['width'])
            c_h = int(self.canvas['height'])
            if self._canvas_image_id is None:
                self._canvas_image_id = self.canvas.create_image(c_w//2, c_h//2, image=tk_img)
            else:
                self.canvas.itemconfigure(self._canvas_image_id, image=tk_img)
        try:
            self.canvas.after(0, _do)
        except Exception:
            # canvas may be destroyed
            pass

    def _play_loop_cv2(self):
        try:
            cap = self._cap
            # fallback fps
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            if fps <= 0:
                fps = 25.0
            frame_delay = 1.0 / fps
            while True:
                with self._lock:
                    if not self._playing or self._cap is None:
                        break
                    ret, frame = self._cap.read()
                if not ret:
                    break
                # convert BGR -> RGB
                try:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                except Exception:
                    # if conversion fails, keep raw
                    pass
                pil = Image.fromarray(frame)
                # resize to fit canvas while keeping aspect ratio
                c_w = int(self.canvas['width'])
                c_h = int(self.canvas['height'])
                pil.thumbnail((c_w, c_h), Image.LANCZOS)
                self._update_canvas_image(pil)
                time.sleep(frame_delay)
        finally:
            with self._lock:
                self._playing = False
                if self._cap:
                    try:
                        self._cap.release()
                    except Exception:
                        pass
                    self._cap = None

    def _play_loop_moviepy(self):
        try:
            clip = self._clip
            fps = getattr(clip, "fps", None) or 25.0
            duration = clip.duration or 0.0
            # step through frames by timestamp (this is slower than cv2 but works)
            t = 0.0
            frame_delay = 1.0 / fps
            while True:
                with self._lock:
                    if not self._playing or self._clip is None:
                        break
                if t >= duration:
                    break
                try:
                    frame = clip.get_frame(t)  # returns RGB ndarray
                except Exception:
                    break
                try:
                    pil = Image.fromarray(frame)
                except Exception:
                    break
                c_w = int(self.canvas['width'])
                c_h = int(self.canvas['height'])
                pil.thumbnail((c_w, c_h), Image.LANCZOS)
                self._update_canvas_image(pil)
                time.sleep(frame_delay)
                t += frame_delay
        finally:
            with self._lock:
                self._playing = False
                if self._clip:
                    try:
                        self._clip.close()
                    except Exception:
                        pass
                    self._clip = None