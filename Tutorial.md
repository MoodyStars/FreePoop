```markdown
# Tutorial — FreePoop 0.5 Deluxe
FreePoop 0.5 — Super Deluxe is a Tkinter-based scaffold for creating YouTube Poop (YTP) style videos: chaotic edits, stutter loops, scrambles, YTP tennis rounds, and YTPMVs. This tutorial explains how to install, run, and use the app; describes the major UI controls and effect toggles; and gives tips and troubleshooting steps for common problems on Windows 8.1 + Python 3.9.

> Warning and ethics
> - Many Poopisms intentionally include sudden loud audio ("ear-rape") and flashing imagery ("eye-rape"). These can cause discomfort or medical harm (hearing damage, seizures). Use these effects responsibly and always warn viewers.
> - Respect copyright. This tool is for remix/edit projects and experimentation. Do not upload sources or derivative works that violate copyright law or platform rules.

Contents
- Quick start (install & run)
- UI walkthrough
- Effects explained (what each toggle does)
- Modes: Deluxe, YTP Tennis, YTPMV
- Presets & "AI year" style selector
- Tips for producing YTP content
- Troubleshooting (ffmpeg, MoviePy, OpenCV)
- Advanced integrations (yt-dlp, VapourSynth, Pygame)
- Contribution & license

---

## Quick start (Windows 8.1, Python 3.9)

1. Create a virtual environment (recommended)
   - Open a command prompt and run:
     python -m venv venv
     venv\Scripts\activate

2. Upgrade pip and install packages
   - python -m pip install --upgrade pip setuptools wheel
   - python -m pip install moviepy pillow numpy requests imageio imageio-ffmpeg
   - Optional (recommended for faster preview): python -m pip install opencv-python
     - If opencv-python fails on Win8.1, download a cp39 wheel from Christoph Gohlke's site and pip install that wheel.

3. Ensure ffmpeg is installed and on PATH
   - MoviePy requires ffmpeg. Download a static ffmpeg build for Windows and add ffmpeg.exe to your PATH.

4. Run FreePoop
   - From the project folder:
     python main.py

---

## UI walkthrough

Top area
- Title and About button.

Left column — Source browsers
- Video files (local): Add local video files (mp4, mov, avi, mkv, wmv, webm). Use "Add" to pick files.
- Audio / Sounds / Music: Add mp3/wav/ogg/m4a soundtracks, SFX, music.
- Images / GIFs: Add images or animated GIFs to be used as visual clips or overlays.
- Transition clips: Short clips inserted between segments.
- Online items (URLs): Register direct URLs (Internet Archive, direct mp4/gif links). At render time the app attempts to download them (placeholder downloader). For robust downloading use the yt-dlp integration (see Advanced integrations).
- Controls: Remove and Clear to manage lists. Clip count is shown in the center area.

Center — Preview and Effects
- Preview Canvas: Play selected video or chosen file (uses OpenCV if installed, otherwise MoviePy fallback).
- Play Selected Video: Plays the selected local video.
- Stop Preview: Halts playback.
- Thumbnail: Quickly show a first-frame thumbnail.
- Effects & Modes: A grid of checkboxes that toggle Poopisms (stutter, stutter-plus, scramble, reverse, mad-dash, ear/eye-rape, etc.)
- Mode selector:
  - Deluxe Poop — general randomized Poop composition (default).
  - YTP Tennis — clips take turns like a tennis rally; ordering and edits mimic tennis rounds.
  - YTPMV — music-driven editing where a chosen audio track drives the final audio mix.
- AI year: Choose a stylistic era (2006–2025). This toggles subtle defaults in effects and tempo to mimic styles of different YTP eras.

Right — Logs / Progress & Export
- Logs show progress_cb messages and status.
- Progress bar shows percent completion.
- Output filename: Set the export filename (default freepoop_v0.5_output.mp4).
- Generate / Export: Starts the render process in a background thread (GUI remains responsive).

---

## Effects explained (what the toggles do)

These implementations are scaffolded and approximate classic "Poopisms". Many are intentionally simplistic placeholders so you can swap in custom DSP or VapourSynth filters.

- Stutter Loop — Repeats a short subclip (visual and audio) several times to create a stutter. Good for rhythmic edits.
- Stutter Loop Plus — Repeats the subclip but applies slightly different effects to each repeat (pitch shifts, small speed ramps, color tints).
- Stutter Loop Minus — Repeats only the audio or removes visuals (black screen or alternate reaction clip), an older YTP technique.
- Split Stutter — A stutter affecting only audio or only video (e.g., keep audio normal, loop visuals).
- Scramble / Random Chop — Chop clips into many small pieces (frames or short intervals), shuffle them randomly, and reassemble. Creates chaotic grammar degradation.
- Reverse / Forward-Reverse / Backward-Forward — Reverse short subclips; combine forward+reverse variants for comedic effect.
- Mad Dash — Speed up parts and layer heavy effects (color flashes, strobe-like overlays).
- Panning — Simulate camera pan by cropping and moving the visible window across frames.
- Staredown / Freeze Frame — Hold a still frame (usually a face) for comedic effect, optionally zoom or pan the freeze.
- Zoom-In / Mysterious Zoom — Slow zoom towards a face with an extending stare.
- Ear Rape — Aggressively amplify an audio sample (DANGEROUS for viewers). Use only with warnings; avoid in public uploads without disclaimers.
- Eye Rape — Bright flashing/high-contrast color effects (can trigger seizures). Avoid or add warnings.
- Pitch Shifting / Vocoding — Pitch changes or vocoder-like processing to create singing or robotic voices. Use external audio tools for best quality (Audacity, sox).
- G-Major — Audio effect/meme: shift pitch and pair with red/demonic tint. Implemented as a simple audio amplitude/pitch change + color tint stub.
- Swirl / Distortion — Image distortions; many editors (Vegas, After Effects) have built-in versions. Scaffold uses simple placeholder overlays.
- Chroma Key — Key out greenscreen hues to overlay assets.
- MLG — Adds MLG-style overlays (soundboard SFX, sunglasses, overlays). Use external asset packs for authentic MLG.

Important: the GUI offers toggles that set pipeline flags; you can extend renderer functions for sophisticated, frame-accurate variants.

---

## Modes & presets

- Deluxe (default) — Random chopping, stutters, overlays. Balanced tempo and effects.
- YTP Tennis — Clips alternate like a rally; good for cooperative collab rounds. Use short clip durations so rounds feel fast.
- YTPMV — Focus on matching visuals to a chosen music/audio track. Try trimming clips to beat intervals for better results.

AI Year (2006–2025)
- This slider only changes internal heuristic defaults (amount of eye/ear-rape, crop/zoom aggressiveness, repeat density) to approximate "old-school" vs "modern" YTP aesthetics. It's a seed for stylistic presets rather than an AI model.

---

## Tips for producing good YTPs

1. Source selection
   - Short, expressive clips with clear emotive faces work best for stares and stutters.
   - Use clean audio stems for vocals if you plan to pitch-shift or vocode.

2. Keep edits musical
   - Even simple rhythmic chopping benefits from matching cuts to beats—try a constant tempo for easier alignment.

3. Use preview often
   - Preview small sections before full render; MoviePy render can be slow for long outputs.

4. Work iteratively
   - Export short test renders (10–30 seconds) when trying out heavy effects or ear/eye-rape to ensure safety and desired result.

5. Backup assets
   - Keep original sources separate. The tool creates temporary files during processing; preserve originals to re-edit.

---

## Troubleshooting

Common errors and how to fix them:

1. "ModuleNotFoundError: No module named 'cv2'"
   - Install opencv-python in the same Python environment used to run the app:
     python -m pip install opencv-python
   - If pip fails on Win8.1, download a cp39 wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv and pip install that wheel.
   - The preview module falls back to MoviePy if cv2 is not present.

2. "write_videofile() got an unexpected keyword argument 'progress_bar'"
   - Different MoviePy versions accept different kwargs. The renderer includes a robust writer that:
     - Inspects write_videofile signature and passes only supported kwargs,
     - Retries with progressively smaller kwarg sets,
     - Falls back to a frame-export + ffmpeg assembly if necessary.
   - If you still see errors, run the program and copy the full traceback to the logs; the tutorial/logs will surface which write strategy was attempted.

3. ffmpeg errors (missing codec or not found)
   - Ensure ffmpeg is installed and on PATH. In Windows:
     - Download a static ffmpeg build, extract, and add the directory containing ffmpeg.exe to the PATH environment variable.
     - Verify with: ffmpeg -version

4. MoviePy compatibility issues
   - Newer stable MoviePy versions (>=1.0) are recommended. If you must use an older MoviePy (e.g., 0.2.2.02), expect some API differences. Consider upgrading or paste the write_videofile traceback so the writer can be adapted.

5. Slow rendering / out of memory
   - Use shorter test renders.
   - If running into memory pressure, increase swap/virtual memory or render in lower resolutions. The renderer resizes clips to reasonable defaults; reduce target resolution if needed.

6. Network/online downloads fail
   - The included download_url_placeholder is a basic requests-based downloader for direct links. For robust downloads from YouTube/Internet Archive use yt-dlp integration (see below).

---

## Advanced integrations (recommended next steps)

1. yt-dlp (recommended for robust online downloads)
   - Install: python -m pip install yt-dlp
   - Replace utils.download_url_placeholder with a wrapper that calls yt-dlp, downloads best mp4/webm and returns a local filename. Use ARGS to prefer direct mp4 and limit formats if needed.

2. VapourSynth / AviSynth
   - Preprocess clips with VapourSynth scripts (.vpy) for advanced filters (deinterlacing, denoising, tempo-preserving pitch shift). Workflow:
     - Add a preprocessing step that writes a temp mp4/wav that MoviePy consumes.
     - Integrate a UI field to point to a .vpy script per-source or global.

3. Pygame preview / scrubbing window
   - A Pygame window offers more advanced realtime control. Keep Tkinter for file management and spawn a Pygame window for playback and keyboard scrubbing.

4. DSP & audio
   - For high-quality pitch shifting and vocoding, integrate librosa, sox or call Audacity macros. MoviePy’s audio effects are limited; external tools give better quality.

---

## Contribution, customization, and development notes

- The project is scaffolded to be modular. Look for:
  - gui.py — UI wiring and lists
  - preview.py — played frames (cv2 or MoviePy fallback)
  - renderer.py — the generation pipeline (where effects are applied)
  - utils.py — helpers and download placeholder
- To add a new Poopism: implement a function in renderer.py that accepts a clip and returns a modified clip; add a toggle in gui.py and pass the flag into generate_deluxe_poop.
- To add presets: create a JSON or Python dict mapping preset names to effect toggles and expose a dropdown in the GUI.

---

## Example quick workflow

1. Add 3 short video clips (or images/gifs).
2. Add 1 audio/music track.
3. Toggle "Stutter Loop" and "Mad Dash", pick Mode = "YTPMV", AI year = 2012.
4. Set output filename, click Generate / Export.
5. Inspect logs; if writing fails due to MoviePy compatibility, the renderer will attempt alternative write paths or fallback to ffmpeg frame-export.

---

## License & credits
- FreePoop is a user-contributed scaffold. Reuse and extend it as you like, but respect third-party copyright.
- Credits: scaffold and examples inspired by typical MoviePy / Tkinter patterns and YouTube Poop community techniques.

```