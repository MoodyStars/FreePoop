# gui.py
# Tkinter GUI for FreePoop 0.5 — Super Deluxe
# - multiple source browsers (local + online entry)
# - preview play/stop
# - clip count
# - effect toggles and mode switches
# - Generate/Export uses renderer.generate_deluxe_poop(...)

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from preview import VideoPreview
from renderer import generate_deluxe_poop
from utils import ensure_dir, ensure_ext, download_url_placeholder

APP_TITLE = "FreePoop 0.5 — Super Deluxe"

class FreePoopGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x780")
        self.create_widgets()
        self.video_preview = VideoPreview(self.preview_canvas)
        self.render_thread = None

    def create_widgets(self):
        # top toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=6, pady=4)
        ttk.Label(toolbar, text=APP_TITLE).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="About", command=self.show_about).pack(side=tk.RIGHT)

        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left: sources
        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)

        self.video_list = self._make_source_block(left, "Video files (local)", self.add_video_files, self.remove_selected, self.clear_videos, allow_online=True)
        self.audio_list = self._make_source_block(left, "Audio / Sounds / Music", self.add_audio_files, self.remove_selected, self.clear_audio, allow_online=True)
        self.image_list = self._make_source_block(left, "Images", self.add_image_files, self.remove_selected, self.clear_images, allow_online=True)
        self.gif_list = self._make_source_block(left, "GIFs", self.add_gif_files, self.remove_selected, self.clear_gifs, allow_online=True)
        self.transition_list = self._make_source_block(left, "Transition clips", self.add_transition_files, self.remove_selected, self.clear_transitions, allow_online=False)
        self.online_list = self._make_source_block(left, "Online items (URLs)", None, self.remove_selected_online, self.clear_online, allow_online=False, show_listbox=True)

        # center: preview and effect toggles
        center = ttk.Frame(main)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        preview_frame = ttk.LabelFrame(center, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.preview_canvas = tk.Canvas(preview_frame, width=720, height=405, bg="black")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        pv_ctrl = ttk.Frame(preview_frame)
        pv_ctrl.pack()
        ttk.Button(pv_ctrl, text="Play Selected Video", command=self.on_play_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(pv_ctrl, text="Stop Preview", command=self.on_stop_preview).pack(side=tk.LEFT, padx=3)
        ttk.Button(pv_ctrl, text="Play File...", command=self.on_choose_play_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(pv_ctrl, text="Thumbnail", command=self.show_thumbnail).pack(side=tk.LEFT, padx=3)

        # Effects and mode controls
        effects_frame = ttk.LabelFrame(center, text="Effects & Modes")
        effects_frame.pack(fill=tk.X, padx=4, pady=4)
        # effects checklist
        self.effects_vars = {}
        effects = [
            ("Stutter Loop", "stutter"),
            ("Stutter Loop Plus", "stutter_plus"),
            ("Stutter Loop Minus", "stutter_minus"),
            ("Split Stutter", "split_stutter"),
            ("Scramble / Random Chop", "scramble"),
            ("Reverse", "reverse"),
            ("Mad Dash (speedy)", "mad_dash"),
            ("Panning", "panning"),
            ("Staredown / Freeze", "stare"),
            ("Zoom-In", "zoom"),
            ("Ear Rape (loud)", "ear_rape"),
            ("Eye Rape (flashy)", "eye_rape"),
            ("Pitch Shift / Vocoder-ish", "pitch_shift"),
            ("G-Major", "g_major"),
            ("Swirl", "swirl"),
            ("Chroma Key (green)", "chroma"),
            ("MLG / Overlays", "mlg"),
        ]
        row = 0
        for i, (label, key) in enumerate(effects):
            var = tk.BooleanVar(value=False)
            self.effects_vars[key] = var
            cb = ttk.Checkbutton(effects_frame, text=label, variable=var)
            cb.grid(row=row, column=(i%3), sticky=tk.W, padx=4, pady=2)
            if (i+1)%3 == 0:
                row += 1

        # Modes and other controls
        mode_frame = ttk.Frame(effects_frame)
        mode_frame.grid(row=10, column=0, columnspan=3, sticky=tk.W, pady=6)
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="deluxe")
        ttk.Radiobutton(mode_frame, text="Deluxe Poop", variable=self.mode_var, value="deluxe").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(mode_frame, text="YTP Tennis", variable=self.mode_var, value="tennis").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(mode_frame, text="YTPMV (music)", variable=self.mode_var, value="ytpmv").pack(side=tk.LEFT, padx=4)

        ttk.Label(mode_frame, text="AI year:").pack(side=tk.LEFT, padx=(12,2))
        self.ai_year = tk.IntVar(value=2020)
        ttk.Spinbox(mode_frame, from_=2006, to=2025, textvariable=self.ai_year, width=6).pack(side=tk.LEFT)

        # overlay options
        overlay_frame = ttk.LabelFrame(center, text="Overlay / Count / Export")
        overlay_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(overlay_frame, text="Clip count:").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.clip_count_var = tk.IntVar(value=0)
        ttk.Label(overlay_frame, textvariable=self.clip_count_var).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(overlay_frame, text="Output filename:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=4)
        self.output_entry = ttk.Entry(overlay_frame)
        self.output_entry.insert(0, "freepoop_v0.5_output.mp4")
        self.output_entry.grid(row=1, column=1, sticky=tk.W, padx=4, pady=4)
        ttk.Button(overlay_frame, text="Generate / Export", command=self.on_generate).grid(row=2, column=0, columnspan=2, pady=6)

        # Right: logs and online preview items
        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=4, pady=4)
        log_frame = ttk.LabelFrame(right, text="Logs / Progress")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, width=50, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.progress = ttk.Progressbar(log_frame, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(fill=tk.X, padx=4, pady=4)
        # quick help
        help_frame = ttk.LabelFrame(right, text="Quick Help")
        help_frame.pack(fill=tk.X, pady=4)
        ttk.Label(help_frame, text="Add local files with Add buttons. Use 'Add Online' to register a URL (download happens at render).").pack(anchor=tk.W, padx=4)

    def _make_source_block(self, parent, title, add_cmd, remove_cmd, clear_cmd, allow_online=False, show_listbox=True):
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill=tk.X, pady=4)
        if show_listbox:
            listbox = tk.Listbox(frame, height=4, selectmode=tk.SINGLE, width=50)
            listbox.pack(side=tk.LEFT, padx=4, pady=4)
        else:
            listbox = None
        btns = ttk.Frame(frame)
        btns.pack(side=tk.LEFT, padx=4)
        if add_cmd:
            ttk.Button(btns, text="Add", command=add_cmd).pack(fill=tk.X, pady=2)
        if allow_online:
            ttk.Button(btns, text="Add Online (URL)", command=lambda lb=listbox: self.add_online_url(lb)).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Remove", command=lambda lb=listbox: self.remove_selected(lb)).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Clear", command=lambda lb=listbox: clear_cmd()).pack(fill=tk.X, pady=2)
        return listbox

    # Source add / remove handlers
    def add_video_files(self):
        files = filedialog.askopenfilenames(title="Select video files", filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv *.wmv *.webm"), ("All", "*.*")])
        for f in files:
            self.video_list.insert(tk.END, f)
            self.log(f"Added video: {f}")
        self.update_clip_count()

    def add_audio_files(self):
        files = filedialog.askopenfilenames(title="Select audio files", filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a"), ("All", "*.*")])
        for f in files:
            self.audio_list.insert(tk.END, f)
            self.log(f"Added audio: {f}")
        self.update_clip_count()

    def add_image_files(self):
        files = filedialog.askopenfilenames(title="Select images", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All", "*.*")])
        for f in files:
            self.image_list.insert(tk.END, f)
            self.log(f"Added image: {f}")
        self.update_clip_count()

    def add_gif_files(self):
        files = filedialog.askopenfilenames(title="Select GIFs", filetypes=[("GIF", "*.gif"), ("All", "*.*")])
        for f in files:
            self.gif_list.insert(tk.END, f)
            self.log(f"Added gif: {f}")
        self.update_clip_count()

    def add_transition_files(self):
        files = filedialog.askopenfilenames(title="Select transition clips", filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv"), ("All", "*.*")])
        for f in files:
            self.transition_list.insert(tk.END, f)
            self.log(f"Added transition: {f}")

    def add_online_url(self, listbox):
        url = simpledialog.askstring("Add online URL", "Paste URL (Internet Archive, direct MP4/GIF, or other):")
        if not url:
            return
        # store URL in the dedicated online list
        self.online_list.insert(tk.END, url)
        self.log(f"Registered online URL: {url}")
        self.update_clip_count()

    def remove_selected(self, listbox=None):
        if listbox is None:
            return
        sel = listbox.curselection()
        if sel:
            idx = sel[0]
            val = listbox.get(idx)
            listbox.delete(idx)
            self.log(f"Removed: {val}")
            self.update_clip_count()

    def remove_selected_online(self, listbox=None):
        self.remove_selected(self.online_list)

    def clear_videos(self):
        self.video_list.delete(0, tk.END); self.log("Cleared video sources"); self.update_clip_count()
    def clear_audio(self):
        self.audio_list.delete(0, tk.END); self.log("Cleared audio sources"); self.update_clip_count()
    def clear_images(self):
        self.image_list.delete(0, tk.END); self.log("Cleared image sources"); self.update_clip_count()
    def clear_gifs(self):
        self.gif_list.delete(0, tk.END); self.log("Cleared gifs"); self.update_clip_count()
    def clear_transitions(self):
        self.transition_list.delete(0, tk.END); self.log("Cleared transitions")
    def clear_online(self):
        self.online_list.delete(0, tk.END); self.log("Cleared online items"); self.update_clip_count()

    def update_clip_count(self):
        count = len(self.video_list.get(0, tk.END)) + len(self.gif_list.get(0, tk.END)) + len(self.image_list.get(0, tk.END))
        self.clip_count_var.set(count)

    # Preview handlers
    def on_play_selected(self):
        sel = self.video_list.curselection()
        if not sel:
            messagebox.showinfo("No selection", "Select a video from the Video sources list to preview.")
            return
        path = self.video_list.get(sel[0])
        try:
            self.video_preview.play(path)
        except Exception as e:
            messagebox.showerror("Preview error", str(e))

    def on_stop_preview(self):
        self.video_preview.stop()

    def on_choose_play_file(self):
        file = filedialog.askopenfilename(title="Choose a file to preview", filetypes=[("Video & GIF", "*.mp4 *.avi *.mov *.gif *.mkv *.wmv *.webm"), ("All", "*.*")])
        if file:
            try:
                self.video_preview.play(file)
            except Exception as e:
                messagebox.showerror("Preview error", str(e))

    def show_thumbnail(self):
        sel = self.video_list.curselection()
        if not sel:
            messagebox.showinfo("No selection", "Select a video to create a thumbnail preview.")
            return
        path = self.video_list.get(sel[0])
        # we use preview to display the first frame as a quick thumbnail
        try:
            self.video_preview.play(path)
        except Exception as e:
            messagebox.showerror("Preview error", str(e))

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
            "transitions": list(self.transition_list.get(0, tk.END)),
            "online": list(self.online_list.get(0, tk.END))
        }
        effects = {k: bool(v.get()) for k, v in self.effects_vars.items()}
        options = {
            "mode": self.mode_var.get(),
            "ai_year": int(self.ai_year.get()),
            "effects": effects
        }

        # disable controls
        self.log("Starting generation...")
        self.progress['value'] = 0
        self.generate_btn_state(False)

        def progress_cb(percent, message=None):
            try:
                if percent is not None:
                    self.progress['value'] = percent
                if message:
                    self.log(message)
                self.update_idletasks()
            except Exception:
                pass

        def done_cb(success, message):
            self.generate_btn_state(True)
            if success:
                self.progress['value'] = 100
                self.log(f"Generation finished: {message}")
                messagebox.showinfo("Finished", f"Generated video: {message}")
            else:
                self.log(f"Generation failed: {message}")
                messagebox.showerror("Error", f"Generation failed: {message}")

        def worker():
            try:
                # attempt to download online items into tmp files (placeholder)
                local_online = []
                for u in sources.get("online", []):
                    self.log(f"Downloading online item (placeholder): {u}")
                    try:
                        local_path = download_url_placeholder(u)
                        local_online.append(local_path)
                        self.log(f"Downloaded: {local_path}")
                    except Exception as e:
                        self.log(f"Failed to download {u}: {e}")
                # append downloaded online items into videos if they look like video/gif
                sources['videos'] = list(sources.get('videos', [])) + local_online
                generate_deluxe_poop(sources, out, options=options, progress_cb=progress_cb)
                done_cb(True, out)
            except Exception as e:
                done_cb(False, str(e))

        self.render_thread = threading.Thread(target=worker, daemon=True)
        self.render_thread.start()

    def generate_btn_state(self, enabled):
        # find the Generate button and enable/disable
        for child in self.winfo_children():
            pass
        # simpler: find buttons by text (not ideal but okay for scaffold)
        for w in self.winfo_children():
            try:
                for btn in w.winfo_children():
                    if isinstance(btn, ttk.Button) and btn.cget("text").startswith("Generate"):
                        btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
            except Exception:
                continue

    # Logging helper
    def log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def show_about(self):
        messagebox.showinfo("About", APP_TITLE + "\nFreePoop 0.5 — Super Deluxe\nScaffold for YTP generation. See README for installation notes.")