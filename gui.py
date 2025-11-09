# gui.py
# Tkinter GUI for FreePoop YTP Generator

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from preview import VideoPreview
from renderer import generate_deluxe_poop
from utils import ensure_dir, ensure_ext

class FreePoopGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FreePoop YTP Generator — Super Deluxe")
        self.geometry("1100x700")
        self.create_widgets()
        self.video_preview = VideoPreview(self.preview_canvas)
        self.render_thread = None

    def create_widgets(self):
        # Left frame: sources
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        # Video sources
        self.video_list = self._make_source_frame(left, "Video sources", 
                                                  [("Add", self.add_video_files), 
                                                   ("Remove", self.remove_selected_video), 
                                                   ("Clear", self.clear_videos)])
        # Audio sources
        self.audio_list = self._make_source_frame(left, "Audio sources", 
                                                  [("Add", self.add_audio_files),
                                                   ("Remove", self.remove_selected_audio),
                                                   ("Clear", self.clear_audio)])
        # Image sources
        self.image_list = self._make_source_frame(left, "Image sources", 
                                                  [("Add", self.add_image_files),
                                                   ("Remove", self.remove_selected_image),
                                                   ("Clear", self.clear_images)])
        # GIF sources
        self.gif_list = self._make_source_frame(left, "GIF sources", 
                                                [("Add", self.add_gif_files),
                                                 ("Remove", self.remove_selected_gif),
                                                 ("Clear", self.clear_gifs)])
        # Output controls
        out_frame = ttk.LabelFrame(left, text="Export")
        out_frame.pack(fill=tk.X, pady=6)
        ttk.Label(out_frame, text="Output filename:").pack(anchor=tk.W)
        self.output_entry = ttk.Entry(out_frame)
        self.output_entry.insert(0, "freepoop_output.mp4")
        self.output_entry.pack(fill=tk.X, padx=4, pady=2)

        self.generate_btn = ttk.Button(out_frame, text="Generate Deluxe Poop", command=self.on_generate)
        self.generate_btn.pack(fill=tk.X, padx=4, pady=6)

        self.progress = ttk.Progressbar(out_frame, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(fill=tk.X, padx=4, pady=2)

        # Right frame: preview and logs
        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Preview area
        preview_frame = ttk.LabelFrame(right, text="Video Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas = tk.Canvas(preview_frame, width=640, height=360, bg="black")
        self.preview_canvas.pack(padx=6, pady=6)

        ctrl = ttk.Frame(preview_frame)
        ctrl.pack()
        ttk.Button(ctrl, text="Play Selected Video", command=self.on_play_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="Stop Preview", command=self.on_stop_preview).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="Play Preview File...", command=self.on_choose_play_file).pack(side=tk.LEFT, padx=4)

        # Log area
        log_frame = ttk.LabelFrame(right, text="Logs")
        log_frame.pack(fill=tk.BOTH, expand=False, pady=6)
        self.log_text = tk.Text(log_frame, height=8)
        self.log_text.pack(fill=tk.BOTH, padx=6, pady=6)

    def _make_source_frame(self, parent, title, buttons):
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill=tk.X, pady=4)
        listbox = tk.Listbox(frame, height=5, selectmode=tk.SINGLE, width=50)
        listbox.pack(side=tk.LEFT, padx=4, pady=4)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.LEFT, padx=4)
        for (t, cmd) in buttons:
            ttk.Button(btn_frame, text=t, command=cmd).pack(fill=tk.X, pady=2)
        return listbox

    # Add/Remove handlers for each source type
    def add_video_files(self):
        files = filedialog.askopenfilenames(title="Select video files", filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv *.webm"), ("All files", "*.*")])
        for f in files:
            self.video_list.insert(tk.END, f)
            self.log(f"Added video: {f}")

    def remove_selected_video(self):
        sel = self.video_list.curselection()
        if sel:
            idx = sel[0]
            val = self.video_list.get(idx)
            self.video_list.delete(idx)
            self.log(f"Removed video: {val}")

    def clear_videos(self):
        self.video_list.delete(0, tk.END)
        self.log("Cleared video sources")

    def add_audio_files(self):
        files = filedialog.askopenfilenames(title="Select audio files", filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a"), ("All files", "*.*")])
        for f in files:
            self.audio_list.insert(tk.END, f)
            self.log(f"Added audio: {f}")

    def remove_selected_audio(self):
        sel = self.audio_list.curselection()
        if sel:
            idx = sel[0]; val = self.audio_list.get(idx); self.audio_list.delete(idx)
            self.log(f"Removed audio: {val}")

    def clear_audio(self):
        self.audio_list.delete(0, tk.END); self.log("Cleared audio sources")

    def add_image_files(self):
        files = filedialog.askopenfilenames(title="Select images", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")])
        for f in files:
            self.image_list.insert(tk.END, f); self.log(f"Added image: {f}")

    def remove_selected_image(self):
        sel = self.image_list.curselection()
        if sel:
            idx = sel[0]; val = self.image_list.get(idx); self.image_list.delete(idx); self.log(f"Removed image: {val}")

    def clear_images(self):
        self.image_list.delete(0, tk.END); self.log("Cleared image sources")

    def add_gif_files(self):
        files = filedialog.askopenfilenames(title="Select GIFs", filetypes=[("GIF", "*.gif"), ("All files", "*.*")])
        for f in files:
            self.gif_list.insert(tk.END, f); self.log(f"Added gif: {f}")

    def remove_selected_gif(self):
        sel = self.gif_list.curselection()
        if sel:
            idx = sel[0]; val = self.gif_list.get(idx); self.gif_list.delete(idx); self.log(f"Removed gif: {val}")

    def clear_gifs(self):
        self.gif_list.delete(0, tk.END); self.log("Cleared gif sources")

    # Preview handlers
    def on_play_selected(self):
        sel = self.video_list.curselection()
        if not sel:
            messagebox.showinfo("No selection", "Select a video from the Video sources list to preview.")
            return
        path = self.video_list.get(sel[0])
        self.video_preview.play(path)

    def on_stop_preview(self):
        self.video_preview.stop()

    def on_choose_play_file(self):
        file = filedialog.askopenfilename(title="Choose a file to preview", filetypes=[("Video & GIF", "*.mp4 *.avi *.mov *.gif *.mkv *.webm"), ("All files", "*.*")])
        if file:
            self.video_preview.play(file)

    # Generate handler
    def on_generate(self):
        out = self.output_entry.get().strip()
        if not out:
            messagebox.showerror("Output required", "Specify an output filename.")
            return
        out = ensure_ext(out, ".mp4")
        out_dir = os.path.dirname(out) or "."
        ensure_dir(out_dir)
        sources = {
            "videos": list(self.video_list.get(0, tk.END)),
            "audios": list(self.audio_list.get(0, tk.END)),
            "images": list(self.image_list.get(0, tk.END)),
            "gifs": list(self.gif_list.get(0, tk.END)),
        }
        # disable controls
        self.generate_btn.config(state=tk.DISABLED)
        self.log("Starting generation...")
        def progress_cb(percent, message=None):
            try:
                self.progress['value'] = percent
                if message:
                    self.log(message)
                self.update_idletasks()
            except Exception:
                pass
        def done_cb(success, message):
            self.generate_btn.config(state=tk.NORMAL)
            if success:
                self.progress['value'] = 100
                self.log(f"Generation finished: {message}")
                messagebox.showinfo("Finished", f"Generated video: {message}")
            else:
                self.log(f"Generation failed: {message}")
                messagebox.showerror("Error", f"Generation failed: {message}")

        # Start generation in a thread
        def worker():
            try:
                generate_deluxe_poop(sources, out, progress_cb=progress_cb)
                done_cb(True, out)
            except Exception as e:
                done_cb(False, str(e))
        self.render_thread = threading.Thread(target=worker, daemon=True)
        self.render_thread.start()

    # Logging helper
    def log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)