# Changelog

## 2025-12-22 — Recent changes

- Fix: Force ffmpeg stream mapping when muxing final video+audio to avoid wrong audio stream being used.
- Fix: Trim only leading silence for TTS MP3s to avoid chopping trailing speech.
- Fix: Escape single quotes when writing ffmpeg concat list files.
- Hardening: Add retries and exponential backoff for downloads and Pexels API calls; remove partial files on failed downloads.
- UX: Add "Description (optional)" textbox in GUI to override narration text file; presets support `description`.
- UX: Add "Clean old cache" button to remove files from `work/` older than N days (default 30).
- Misc: Remove stale sidecar ASS files when subtitles disabled; suppress text-preview logging when both captions and overlay are disabled.

Files changed (summary):
- `src/videer_gui.py` — presets, cleanup helper, GUI wiring, various hardening fixes
- `src/videer_wsl.py` — parity fixes for CLI

If you'd like, I can commit these changes to git and create a tag/branch.
