# preview.py
# Video preview utility: uses OpenCV to read frames and Pillow to show in Tkinter Canvas

import threading
import time
import cv2
from PIL import Image, ImageTk

class VideoPreview:
    def __init__(self, tk_canvas):
        self.canvas = tk_canvas
        self._playing = False
        self._thread = None
        self._cap = None
        self._canvas_image_id = None
        self._lock = threading.Lock()

    def play(self, path):
        with self._lock:
            self.stop()
            self._cap = cv2.VideoCapture(path)
            if not self._cap.isOpened():
                raise RuntimeError(f"Can't open file for preview: {path}")
            self._playing = True
            self._thread = threading.Thread(target=self._play_loop, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            self._playing = False
            if self._cap:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None

    def _play_loop(self):
        try:
            while True:
                with self._lock:
                    if not self._playing or self._cap is None:
                        break
                    ret, frame = self._cap.read()
                if not ret:
                    # End of file: stop
                    break
                # convert color BGR->RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                # resize to fit canvas while keeping aspect ratio
                c_w = int(self.canvas['width'])
                c_h = int(self.canvas['height'])
                img.thumbnail((c_w, c_h), Image.ANTIALIAS)
                tk_img = ImageTk.PhotoImage(img)
                # tkinter UI update (must be done on main thread) — use after if needed
                def _update(img=tk_img):
                    # keep reference to avoid GC
                    self.canvas.image_ref = img
                    if self._canvas_image_id is None:
                        self._canvas_image_id = self.canvas.create_image(c_w//2, c_h//2, image=img)
                    else:
                        self.canvas.itemconfigure(self._canvas_image_id, image=img)
                try:
                    self.canvas.after(0, _update)
                except Exception:
                    pass
                time.sleep(1.0 / max(self._cap.get(cv2.CAP_PROP_FPS) or 25, 25))
        finally:
            with self._lock:
                self._playing = False
                if self._cap:
                    try:
                        self._cap.release()
                    except Exception:
                        pass
                    self._cap = None