# Videer — Text → Pexels → Voice → Video

Creates a narrated video from text using:
- Pexels (videos/photos)
- edge-tts (AI voice)
- ffmpeg (render/concat)

## Prereqs (WSL Ubuntu)

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
```

## Setup (inside project)

```bash
cd /home/thasnain/videer_wsl
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install requests edge-tts tqdm
```

Set your Pexels API key in a local `.env` (DO NOT COMMIT this file):

```
PEXELS_API_KEY=your_key_here
```

## Run

```bash
source .venv/bin/activate
python3 -m src.videer_gui
```

Or call the headless pipeline in `src/videer_wsl.py`.

## Notes

- The project writes cache files into `work/` and final outputs into `outputs/`.
- `.env` is ignored by the repository `.gitignore` to avoid leaking API keys.

