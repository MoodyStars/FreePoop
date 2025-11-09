# FreePoop YTP Generator — Super Deluxe (Tkinter)

# What this is
- A desktop GUI scaffold (Tkinter) to build a "YTPoop-style" random splice generator.
- Browsers for video/audio/image/gif sources.
- Preview inside the GUI (OpenCV + Pillow).
- A "Generate" pipeline using MoviePy to assemble a final video.

# Files
- main.py — entry point
- gui.py — main Tkinter UI and interactions
- preview.py — video preview code (OpenCV -> Pillow -> Tkinter canvas)
- renderer.py — the generation / composition code using MoviePy
- utils.py — small utilities

# Notes and warnings
- You asked for Python 3.9 on Windows 8.1 and a specific MoviePy version (0.2.2.02). That version is very old and may not be available via pip or may behave differently than recent MoviePy. If you run into import errors, try using a modern MoviePy (e.g. 1.x) if possible. Code attempts to use generic API calls to be compatible, but you may need to adjust vfx imports.
- The code uses:
  - moviepy
  - opencv-python (cv2)
  - pillow (PIL)
  - numpy
  - (optional) pygame and vapoursynth — there are placeholders for integrating them. Pygame isn't used in the preview code because mixing Pygame and Tkinter display loops is complex; instead video preview uses OpenCV+Pillow.

# Suggested installation (adjust versions to your environment):
- Create and activate a Python 3.9 virtualenv
- pip install moviepy opencv-python pillow numpy tqdm
- If you must try that ancient moviepy: pip install moviepy==0.2.2.02  (may fail; modern pip may not find it)
- For VapourSynth and Pygame install via their recommended installers for Windows

# Running
- python main.py

  # Screenshot

# Limitations
- This is a scaffold; the generation pipeline demonstrates random chopping, ordering, and basic attachments of audio. For production YTP-level effects you'll want to:
  - Add VapourSynth filtering pipelines (deinterlacing, motion blur, advanced color transforms).
  - Use Pygame for advanced real-time preview / audio sync (non-trivial inside Tkinter).
  - Add timeline editing UI, looped preview, and detailed effect controls.
  - Add robust error handling for many video codecs on Windows.

If you want, I can:
- Integrate a Pygame-based preview (separate window) that supports keyboard scrubbing and audio sync.
- Add a VapourSynth hook so users can drop .vpy filter scripts that process sources before composition.
- Expand generation patterns (beat-synced cuts, strobing, heavy speed ramp effects).
- Package as a Windows executable (PyInstaller) with dependency hints for VapourSynth and ffmpeg.

```
