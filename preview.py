# preview.py
# Video preview utility: uses OpenCV if available, otherwise falls back to MoviePy.
# Keeps module-safe imports and works in Python 3.9 Windows.

import threading
import time
from PIL import Image, ImageTk

# lazy import cv2
try:
    import cv2
except Exception:
    cv2 = None

# moviepy fallback
try:
    from moviepy.editor import VideoFileClip
except Exception:
    VideoFileClip = None

class VideoPreview:
    def __init__(self, tk_canvas):
        self.canvas = tk_canvas
        self._playing = False
        self._thread = None
        self._lock = threading.Lock()
        self._canvas_image_id = None
        self._cap = None
        self._clip = None

    def play(self, path):
        with self._lock:
            self.stop()
            # try cv2
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
            # fallback to moviepy
            if VideoFileClip is not None:
                clip = VideoFileClip(path)
                if clip.duration is None:
                    clip.close()
                    raise RuntimeError("Unreadable clip")
                self._clip = clip
                self._playing = True
                self._thread = threading.Thread(target=self._play_loop_moviepy, daemon=True)
                self._thread.start()
                return
            raise RuntimeError("No preview backend available: install opencv-python or moviepy")

    def stop(self):
        with self._lock:
            self._playing = False
            if self._cap:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
            if self._clip:
                try:
                    self._clip.close()
                except Exception:
                    pass
                self._clip = None

    def _update_canvas_image(self, pil_img):
        tk_img = ImageTk.PhotoImage(pil_img)
        def _do():
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
            pass

    def _play_loop_cv2(self):
        try:
            cap = self._cap
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            if fps <= 0:
                fps = 25.0
            delay = 1.0 / fps
            while True:
                with self._lock:
                    if not self._playing or self._cap is None:
                        break
                    ret, frame = self._cap.read()
                if not ret:
                    break
                try:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                except Exception:
                    pass
                pil = Image.fromarray(frame)
                c_w = int(self.canvas['width'])
                c_h = int(self.canvas['height'])
                pil.thumbnail((c_w, c_h), Image.LANCZOS)
                self._update_canvas_image(pil)
                time.sleep(delay)
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
            fps = getattr(clip, "fps", 25.0) or 25.0
            duration = clip.duration or 0.0
            frame_delay = 1.0 / fps
            t = 0.0
            while True:
                with self._lock:
                    if not self._playing or self._clip is None:
                        break
                if t >= duration:
                    break
                try:
                    frame = clip.get_frame(t)
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