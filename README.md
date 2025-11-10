# FreePoop 0.5 — Super Deluxe (Tkinter scaffold)

What this is
- A scaffold GUI to create YouTube Poop–style videos (YTP, YTP tennis, YTPMV).
- Source browsers for local video/audio/images/gifs/transition clips and a list to register online URLs.
- Preview (uses OpenCV if installed, otherwise MoviePy).
- Effects toggles (stutter, scramble, reverse, ear-rape, overlays, etc.) implemented as pipeline flags.
- Export using MoviePy and ffmpeg. Robust write routines to support multiple MoviePy versions.

Files
- main.py — entry point
- gui.py — main Tkinter UI and wiring
- preview.py — preview helper (cv2 or MoviePy fallback)
- renderer.py — generation pipeline implementing many Poopisms (scaffold/hook-based)
- utils.py — helpers including a download placeholder
- README.md — this file

Installation (Windows 8.1, Python 3.9)
1) Create a virtualenv:
   python -m venv venv
   venv\Scripts\activate

2) Upgrade pip and install requirements:
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install moviepy pillow numpy requests imageio imageio-ffmpeg

3) Optional: install OpenCV for faster preview:
   python -m pip install opencv-python
   If that fails on Windows 8.1, download a wheel for cp39 from https://www.lfd.uci.edu/~gohlke/pythonlibs/ and pip install it.

4) Ensure ffmpeg is installed and on PATH. MoviePy uses ffmpeg for rendering. On Windows get ffmpeg builds and add to PATH.

Notes about MoviePy compatibility
- This scaffold tries multiple argument sets for write_videofile since older versions (like 0.2.2.02) accept different kwargs. If you have an ancient MoviePy installed and see errors, consider upgrading to a modern MoviePy (>=1.0), or paste the write_videofile traceback and we'll adapt.

Online downloads
- The GUI registers URLs in a list; at render time a placeholder download (requests) is used for direct file links. For robust downloads (YouTube, Internet Archive, etc.) integrate yt-dlp/yt-dl/ia tools and replace utils.download_url_placeholder with a proper downloader.

Advanced integrations
- VapourSynth / AviSynth: place hooks in the renderer pipeline to preprocess clips (replace _safe_video_clip with a preprocessed tempfile path).
- Pygame: you may prefer a Pygame preview window; current preview uses Tkinter Canvas with OpenCV or MoviePy frame extraction.

Limitations & next steps
- This is a scaffold — effects are deliberately simple and demonstrated as toggles. Many Poopisms (pitch-shifting without tempo change, vocoder, true vocoding, advanced chroma key, eye/ear-rape safe handling) require external tools or DSP libraries (librosa, pydub, sox).
- Overlays produce temporary PNG frames for simple tint/overlay. Replace with real assets for MLG packs, green-screen assets, etc.
- Online download is placeholder: integrate yt-dlp for robust downloads and metadata.
- If you want, I can:
  - implement yt-dlp integration and automatic Internet Archive fetching,
  - add a Pygame preview window and keyboard scrubbing,
  - add a VapourSynth hook for prefiltering clips,
  - or add a seeded deterministic mode and batch presets for classic Poopisms (2006, 2010, 2015, 2020, 2025 styles).

Running
- python main.py

License / attribution
- This code is a user-space scaffold intended for remix/edit tooling. Respect copyright and community rules when using source material.

```
