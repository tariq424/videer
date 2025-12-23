#!/usr/bin/env python3
"""
Videer GUI (WSL) — Text → Pexels → Voice → Video

This version fixes your current state:
- Your segments are written to: work/segments/
- Your GUI previously expected: work/vsegments/  (wrong)
- It also guarantees final assembly outputs:
    work/final_video.mp4
    work/final_audio.m4a
    outputs/final_fixed.mp4
    outputs/final_subbed.mp4 (if overlay enabled)
"""

from __future__ import annotations

import os
import re
import time
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Literal

import requests
from tqdm import tqdm

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog


# =============================================================================
# Constants / Types
# =============================================================================

PEXELS_VIDEO_SEARCH = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_SEARCH = "https://api.pexels.com/v1/search"

DEFAULT_VOICE = "en-US-JennyNeural"

Aspect = Literal["16:9", "9:16"]
QueryStrategy = Literal["basic", "topic_mapped"]
SubStyle = Literal["pop_ass", "plain_srt"]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "for", "with", "as", "at", "by",
    "is", "are", "was", "were", "be", "been", "it", "this", "that", "these", "those", "we", "you",
    "i", "they", "he", "she", "them", "his", "her", "our", "your", "from", "into", "about", "over",
    "replace", "own", "text", "script", "sample", "narration",
}

TOPIC_VISUAL_MAP: Dict[str, str] = {
    "ai": "server racks data center technology",
    "business": "office teamwork meeting",
    "finance": "stock market charts city skyline",
    "health": "doctor hospital wellness",
    "travel": "aerial landscape city drone",
    "motivation": "sunrise mountain runner",
    "news": "city night timelapse newsroom",
    "islam": "mosque skyline prayer sunrise",
}

# ASS colors are in &HAABBGGRR
# Turquoise RGB 40E0D0 -> BGR D0E040 -> &H00D0E040
FONT_COLORS_ASS: Dict[str, str] = {
    "Turquoise (default)": "&H00D0E040",
    "White": "&H00FFFFFF",
    "Yellow": "&H0000FFFF",
    "Pink": "&H00FF80FF",
    "Lime": "&H0000FF00",
}

PRESETS: Dict[str, Dict[str, object]] = {
    "Fast YouTube Shorts": {
        "aspect": "9:16",
        "max_chars": 320,
        "rate": "+12%",
        "query_strategy": "topic_mapped",
        "add_subtitles": True,
        "subtitle_style": "pop_ass",
        "overlay_text": True,
        "font_color": "Turquoise (default)",
        "description": "",
    },
    "Standard (16:9)": {
        "aspect": "16:9",
        "max_chars": 650,
        "rate": "+0%",
        "query_strategy": "basic",
        "add_subtitles": True,
        "subtitle_style": "plain_srt",
        "overlay_text": False,
        "font_color": "White",
        "description": "",
    },
}


# =============================================================================
# Shell helpers
# =============================================================================

def run(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def have(cmd: str) -> bool:
    return subprocess.call(["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"]) == 0


def ensure_tools() -> None:
    if not have("ffmpeg") or not have("ffprobe"):
        raise RuntimeError("ffmpeg/ffprobe not found. Install in WSL: sudo apt install -y ffmpeg")
    if not have("edge-tts"):
        raise RuntimeError("edge-tts not found. Install in venv: pip install edge-tts")


def read_dotenv(dotenv_path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not dotenv_path.exists():
        return env
    for line in dotenv_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("'").strip('"')
    return env


def get_pexels_api_key(project_root: Path) -> str:
    key = (os.environ.get("PEXELS_API_KEY") or "").strip()
    if key:
        return key
    env = read_dotenv(project_root / ".env")
    key = (env.get("PEXELS_API_KEY") or "").strip()
    if key:
        return key
    raise RuntimeError("PEXELS_API_KEY not set. Put it in .env or export it in the shell.")


def safe_name(s: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s).strip("_")
    s = s[:maxlen] if len(s) > maxlen else s
    return s or "clip"


def clean_old_work(workdir: Path, days: int = 30, log: Optional[Callable[[str], None]] = None) -> int:
    """Remove files under `workdir` older than `days` days. Returns number of files removed."""
    cutoff = time.time() - (days * 86400)
    removed = 0
    if not workdir.exists():
        if log:
            log(f"Workdir {workdir} does not exist; nothing to clean.")
        return 0
    for p in workdir.rglob("*"):
        try:
            if p.is_file():
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    removed += 1
            elif p.is_dir():
                try:
                    p.rmdir()
                except Exception:
                    pass
        except Exception:
            pass
    if log:
        log(f"Removed {removed} files older than {days} days from {workdir}")
    return removed


# =============================================================================
# Text chunking (one sentence at a time)
# =============================================================================

_BULLET_PREFIX = re.compile(r"^\s*(?:[-*•]+|\d+[.)])\s+")
_EMPTY_LINE = re.compile(r"^\s*$")


def _split_by_lines_first(text: str) -> List[str]:
    lines: List[str] = []
    for raw in text.splitlines():
        if _EMPTY_LINE.match(raw):
            continue
        line = raw.strip()
        line = _BULLET_PREFIX.sub("", line).strip()
        if line:
            lines.append(line)
    return lines


def split_text_into_blocks(text: str, max_chars: int) -> List[str]:
    """
    Produces blocks for BOTH:
    - audio generation (one block -> one TTS file)
    - caption overlay (one block -> one caption event)

    Rules:
    - split first on non-empty lines
    - then split each line into sentences on . ! ?
    - enforce max_chars by splitting at WORD boundaries
    """
    text = text.strip()
    if not text:
        return []

    base_units = _split_by_lines_first(text)
    if not base_units:
        base_units = [re.sub(r"\s+", " ", text).strip()]

    sentences: List[str] = []
    for unit in base_units:
        unit = re.sub(r"\s+", " ", unit).strip()
        if not unit:
            continue
        parts = [p.strip() for p in _SENT_SPLIT.split(unit) if p.strip()]
        if len(parts) == 1:
            sentences.append(parts[0])
        else:
            sentences.extend(parts)

    blocks: List[str] = []
    for s in sentences:
        if len(s) <= max_chars:
            blocks.append(s)
            continue
        words = s.split()
        cur: List[str] = []
        for w in words:
            candidate = (" ".join(cur + [w])).strip()
            if len(candidate) <= max_chars or not cur:
                cur.append(w)
            else:
                blocks.append(" ".join(cur))
                cur = [w]
        if cur:
            blocks.append(" ".join(cur))

    return blocks


# =============================================================================
# Query strategy
# =============================================================================

def query_keywords_basic(block: str, max_words: int = 6) -> str:
    words = re.findall(r"[a-zA-Z0-9']+", block.lower())
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return " ".join(keywords[:max_words]) if keywords else "abstract background"


def query_topic_mapped(block: str) -> str:
    b = block.lower()
    for topic, visual in TOPIC_VISUAL_MAP.items():
        if topic in b:
            return visual
    return query_keywords_basic(block)


def make_query(block: str, strategy: QueryStrategy) -> str:
    return query_topic_mapped(block) if strategy == "topic_mapped" else query_keywords_basic(block)


# =============================================================================
# Pexels API
# =============================================================================

def pexels_headers(api_key: str) -> dict:
    return {"Authorization": api_key}


def pexels_search_videos(api_key: str, query: str, per_page: int = 6) -> List[dict]:
    retries = 4
    backoff_base = 0.6
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(
                PEXELS_VIDEO_SEARCH,
                headers=pexels_headers(api_key),
                params={"query": query, "per_page": per_page, "page": 1},
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("videos", [])
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff_base * (2 ** (attempt - 1)) + random.random() * 0.2)
                continue
            raise


def pexels_search_photos(api_key: str, query: str, per_page: int = 6) -> List[dict]:
    retries = 4
    backoff_base = 0.6
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(
                PEXELS_PHOTO_SEARCH,
                headers=pexels_headers(api_key),
                params={"query": query, "per_page": per_page, "page": 1},
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("photos", [])
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff_base * (2 ** (attempt - 1)) + random.random() * 0.2)
                continue
            raise


def pick_best_video_url(video_obj: dict, prefer_width: int) -> Optional[str]:
    files = video_obj.get("video_files", []) or []
    mp4s = [f for f in files if (f.get("file_type") or "").lower() == "video/mp4" and f.get("link")]
    if not mp4s:
        mp4s = [f for f in files if f.get("link")]
    if not mp4s:
        return None

    def score(f: dict) -> float:
        w = f.get("width") or 0
        return -abs(w - prefer_width)

    return max(mp4s, key=score).get("link")


def download_url(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Robust download with retries and exponential backoff for transient network errors
    retries = 5
    backoff_base = 0.6
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                with open(out_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=out_path.name) as pbar:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            return
        except Exception as e:
            last_err = e
            try:
                if out_path.exists():
                    out_path.unlink()
            except Exception:
                pass
            if attempt < retries:
                wait = backoff_base * (2 ** (attempt - 1))
                time.sleep(wait + random.random() * 0.2)
                continue
            raise


# =============================================================================
# Audio (edge-tts)
# =============================================================================

def sanitize_for_tts(text: str) -> str:
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"[^\x09\x0a\x0d\x20-\x7E]", "", text)  # drop emojis
    text = re.sub(r"\s+", " ", text).strip()
    return text


def audio_duration_seconds(audio_path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        text=True
    ).strip()
    try:
        return float(out)
    except Exception:
        return 0.0


def trim_silence_mp3_inplace(mp3_path: Path) -> None:
    tmp = mp3_path.with_suffix(".trim.mp3")
    # Only remove leading silence (start) to avoid chopping sentence tails.
    af = (
        "silenceremove="
        "start_periods=1:start_duration=0.06:start_threshold=-45dB"
    )
    run([
        "ffmpeg", "-y",
        "-i", str(mp3_path),
        "-af", af,
        "-c:a", "libmp3lame", "-q:a", "4",
        str(tmp),
    ])
    tmp.replace(mp3_path)


def tts_edge_validated(
    text: str,
    out_mp3: Path,
    voice: str,
    rate: str,
    log: Callable[[str], None],
    retries: int = 3,
) -> None:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    clean = sanitize_for_tts(text)
    if not clean:
        raise RuntimeError("TTS block became empty after sanitization.")

    last_err: Optional[str] = None
    for attempt in range(1, retries + 1):
        try:
            if out_mp3.exists():
                out_mp3.unlink()

            run([
                "edge-tts",
                "--text", clean,
                "--voice", voice,
                "--rate", rate,
                "--write-media", str(out_mp3),
            ])

            if not out_mp3.exists() or out_mp3.stat().st_size < 1500:
                raise RuntimeError("edge-tts produced an empty mp3.")

            dur = audio_duration_seconds(out_mp3)
            if dur < 0.20:
                raise RuntimeError(f"mp3 too short ({dur:.3f}s).")

            trim_silence_mp3_inplace(out_mp3)
            dur2 = audio_duration_seconds(out_mp3)
            if dur2 < 0.15:
                raise RuntimeError("mp3 became too short after trimming.")

            return

        except Exception as e:
            last_err = str(e)
            log(f"[WARN] TTS attempt {attempt}/{retries} failed: {last_err}")
            time.sleep(0.4)

    raise RuntimeError(f"TTS failed after {retries} attempts: {last_err}")


# =============================================================================
# Video segments + assembly (FIXED)
# =============================================================================

def vf_for_aspect(aspect: Aspect) -> Tuple[str, str]:
    if aspect == "9:16":
        return ("1080:1920", "1080:1920")
    return ("1920:1080", "1920:1080")


def build_video_segment_from_video(
    video_path: Path,
    duration_sec: float,
    out_path: Path,
    aspect: Aspect
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop_size, scale_target = vf_for_aspect(aspect)
    vf = f"scale={scale_target}:force_original_aspect_ratio=increase,crop={crop_size}"

    run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-t", f"{duration_sec:.3f}",
        "-vf", vf,
        "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_path),
    ])


def build_video_segment_from_photo(
    photo_path: Path,
    duration_sec: float,
    out_path: Path,
    aspect: Aspect
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fps = 30
    frames = max(1, int(duration_sec * fps))
    crop_size, scale_target = vf_for_aspect(aspect)

    vf = (
        f"scale={scale_target}:force_original_aspect_ratio=increase,"
        f"crop={crop_size},"
        f"zoompan=z='min(zoom+0.0008,1.10)':d={frames}:s={scale_target}:fps={fps}"
    )

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(photo_path),
        "-t", f"{duration_sec:.3f}",
        "-vf", vf,
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_path),
    ])


def concat_video_segments(segment_paths: List[Path], out_video: Path) -> None:
    out_video.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_video.parent / "concat_video_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in segment_paths:
            ppos = p.as_posix()
            # Escape single quotes in paths for ffmpeg concat files: ' -> '\''
            p_escaped = ppos.replace("'", "'\\''")
            f.write(f"file '{p_escaped}'\n")

    # Using re-encode concat to be robust (even if minor codec differences exist)
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        str(out_video),
    ])


def concat_audio_to_m4a(audio_paths: List[Path], out_m4a: Path) -> None:
    out_m4a.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_m4a.parent / "concat_audio_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in audio_paths:
            ppos = p.as_posix()
            p_escaped = ppos.replace("'", "'\\''")
            f.write(f"file '{p_escaped}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "aac", "-b:a", "128k",
        str(out_m4a),
    ])


def mux_video_audio(video_mp4: Path, audio_m4a: Path, out_mp4: Path) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y",
        "-i", str(video_mp4),
        "-i", str(audio_m4a),
        # Explicitly map video from input 0 and audio from input 1 so
        # the concatenated TTS audio is used for the whole output.
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_mp4),
    ])


# =============================================================================
# Captions (ASS pop style)
# =============================================================================

def insert_one_linebreak_for_fit(text: str, target_line_len: int) -> str:
    clean = re.sub(r"\s+", " ", text.strip())
    if len(clean) <= target_line_len:
        return clean

    words = clean.split()
    if len(words) < 6:
        return clean

    midpoint = len(clean) // 2
    best_i = None
    best_dist = 10**9
    running = 0
    for i, w in enumerate(words[:-1], start=1):
        running += len(w) + 1
        dist = abs(running - midpoint)
        if dist < best_dist:
            best_dist = dist
            best_i = i

    if not best_i or best_i <= 1 or best_i >= len(words) - 1:
        return clean

    left = " ".join(words[:best_i])
    right = " ".join(words[best_i:])
    if len(left) < 8 or len(right) < 8:
        return clean

    return left + r"\N" + right


def write_ass_pop(
    blocks: List[str],
    durations: List[float],
    out_ass: Path,
    aspect: Aspect,
    font_color_name: str,
) -> None:
    out_ass.parent.mkdir(parents=True, exist_ok=True)

    if aspect == "9:16":
        play_res_x, play_res_y = 1080, 1920
        font_size = 30
        margin_v = 240
        outline = 4
        split_line_target = 34
    else:
        play_res_x, play_res_y = 1920, 1080
        font_size = 42
        margin_v = 90
        outline = 5
        split_line_target = 56

    primary = FONT_COLORS_ASS.get(font_color_name, FONT_COLORS_ASS["Turquoise (default)"])

    def ass_time(t: float) -> str:
        cs = int(round((t - int(t)) * 100))
        s = int(t)
        hh = s // 3600
        mm = (s % 3600) // 60
        ss = s % 60
        return f"{hh}:{mm:02d}:{ss:02d}.{cs:02d}"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,Arial,{font_size},{primary},&H00FFFFFF,&H00000000,&H7F000000,1,0,0,0,100,100,0,0,1,{outline},1,2,80,80,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    anim_prefix = r"{\q2\fscx120\fscy120\t(0,120,\fscx100\fscy100)\fad(50,120)}"

    t = 0.0
    lines: List[str] = [header]
    for txt, dur in zip(blocks, durations):
        start = t
        end = t + max(0.2, dur)

        safe_txt = txt.replace("{", r"\{").replace("}", r"\}")
        safe_txt = insert_one_linebreak_for_fit(safe_txt, split_line_target)

        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Pop,,0,0,0,,{anim_prefix}{safe_txt}\n")
        t = end

    out_ass.write_text("".join(lines), encoding="utf-8")


def burn_in_subtitles(in_video: Path, subs_path: Path, out_video: Path) -> None:
    out_video.parent.mkdir(parents=True, exist_ok=True)
    subs_abs = subs_path.resolve().as_posix().replace("'", r"\'")
    run([
        "ffmpeg", "-y",
        "-i", str(in_video),
        "-vf", f"subtitles='{subs_abs}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "copy",
        str(out_video),
    ])


# =============================================================================
# Build pipeline
# =============================================================================

@dataclass(frozen=True)
class BuildOptions:
    text_path: Path
    text_override: Optional[str]
    out_video: Path
    workdir: Path
    max_chars: int
    voice: str
    rate: str
    aspect: Aspect
    query_strategy: QueryStrategy
    add_subtitles: bool
    subtitle_style: SubStyle
    overlay_text: bool
    font_color_name: str
    throttle_sec: float = 0.4


def build_video(project_root: Path, opts: BuildOptions, log: Callable[[str], None]) -> Tuple[Path, Optional[Path]]:
    ensure_tools()
    api_key = get_pexels_api_key(project_root)

    # Prefer in-UI override text if provided, otherwise read from the text file.
    if getattr(opts, "text_override", None) and str(opts.text_override).strip():
        text = str(opts.text_override)
    else:
        text = opts.text_path.read_text(encoding="utf-8", errors="ignore")
    blocks = split_text_into_blocks(text, max_chars=opts.max_chars)
    if not blocks:
        raise ValueError("Narration is empty (no blocks produced).")

    log(f"[INFO] Blocks created: {len(blocks)}")
    # Only show block previews when captions or overlay are enabled —
    # if the user has both options disabled we avoid any text-related
    # output or side-effects.
    if opts.add_subtitles or opts.overlay_text:
        for i, b in enumerate(blocks[:10], start=1):
            preview = (b[:70] + "…") if len(b) > 70 else b
            log(f"[INFO]   block {i}: {preview}")

    workdir = opts.workdir.expanduser().resolve()
    media_dir = workdir / "media"
    audio_dir = workdir / "audio"
    seg_dir = workdir / "segments"  # IMPORTANT: matches your existing structure
    for d in (media_dir, audio_dir, seg_dir):
        d.mkdir(parents=True, exist_ok=True)

    out_dir = opts.out_video.expanduser().resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Remove stale sidecar caption files when the user has requested no subtitles
    if not opts.add_subtitles:
        for stale in (out_dir / "final_fixed.ass", out_dir / "final_captions.ass"):
            try:
                if stale.exists():
                    stale.unlink()
            except Exception:
                pass

    final_fixed = out_dir / "final_fixed.mp4"
    final_subbed = out_dir / "final_subbed.mp4"

    prefer_width = 1080 if opts.aspect == "9:16" else 1920

    segment_paths: List[Path] = []
    audio_paths: List[Path] = []
    durations: List[float] = []

    for i, block in enumerate(blocks, start=1):
        query = make_query(block, opts.query_strategy)
        base = f"{i:03d}_{safe_name(query)}"
        log(f"[INFO] [{i}/{len(blocks)}] query='{query}'")

        # --- audio clip ---
        audio_path = audio_dir / f"{base}.mp3"
        if not audio_path.exists():
            log("[INFO]   - TTS...")
            tts_edge_validated(block, audio_path, opts.voice, opts.rate, log=log, retries=3)
        dur = audio_duration_seconds(audio_path)
        if dur < 0.2:
            raise RuntimeError(f"Audio duration too small for {audio_path.name}: {dur:.3f}s")
        audio_paths.append(audio_path)
        durations.append(dur)

        # --- segment mp4 (with audio) ---
        seg_path = seg_dir / f"{base}.mp4"
        if seg_path.exists():
            log("[INFO]   - segment cached")
            segment_paths.append(seg_path)
            continue

        video_path: Optional[Path] = None
        photo_path: Optional[Path] = None

        try:
            vids = pexels_search_videos(api_key, query)
            if vids:
                chosen = random.choice(vids)
                url = pick_best_video_url(chosen, prefer_width=prefer_width)
                if url:
                    video_path = media_dir / f"{base}.mp4"
                    log("[INFO]   - downloading video...")
                    download_url(url, video_path)
        except Exception as e:
            log(f"[WARN]   - video search/download failed: {e}")

        if video_path is None:
            try:
                photos = pexels_search_photos(api_key, query)
                if photos:
                    chosen = random.choice(photos)
                    src = chosen.get("src", {}) or {}
                    url = src.get("large2x") or src.get("large") or src.get("original")
                    if url:
                        photo_path = media_dir / f"{base}.jpg"
                        log("[INFO]   - downloading photo...")
                        download_url(url, photo_path)
            except Exception as e:
                log(f"[WARN]   - photo search/download failed: {e}")

        if video_path is None and photo_path is None:
            fallback = "abstract background"
            log(f"[INFO]   - fallback media='{fallback}'")
            vids = pexels_search_videos(api_key, fallback)
            if vids:
                chosen = random.choice(vids)
                url = pick_best_video_url(chosen, prefer_width=prefer_width)
                if url:
                    video_path = media_dir / f"{base}.mp4"
                    download_url(url, video_path)

        log("[INFO]   - building segment...")
        if video_path is not None:
            build_video_segment_from_video(video_path, dur, seg_path, aspect=opts.aspect)
        elif photo_path is not None:
            build_video_segment_from_photo(photo_path, dur, seg_path, aspect=opts.aspect)
        else:
            raise RuntimeError("Could not build segment: no media found.")

        segment_paths.append(seg_path)
        time.sleep(opts.throttle_sec)

    # ===== FIXED FINAL ASSEMBLY =====
    work_final_video = workdir / "final_video.mp4"
    work_final_audio = workdir / "final_audio.m4a"

    log("[INFO] Concatenating segments -> work/final_video.mp4")
    concat_video_segments(segment_paths, work_final_video)

    log("[INFO] Concatenating audio mp3 -> work/final_audio.m4a")
    concat_audio_to_m4a(audio_paths, work_final_audio)

    log("[INFO] Muxing final_fixed.mp4 (video+audio)")
    mux_video_audio(work_final_video, work_final_audio, final_fixed)

    subs_written: Optional[Path] = None
    final_out = final_fixed

    if opts.add_subtitles:
        # When overlay_text is True we will burn the captions into the video.
        # If overlay_text is False, write the captions file with a different
        # name so players do not auto-load the sidecar file next to the MP4.
        if opts.overlay_text:
            subs_path = out_dir / "final_fixed.ass"
        else:
            subs_path = out_dir / "final_captions.ass"
        log(f"[INFO] Writing captions: {subs_path.name} (color: {opts.font_color_name})")
        write_ass_pop(blocks, durations, subs_path, opts.aspect, opts.font_color_name)
        subs_written = subs_path

        if opts.overlay_text:
            log("[INFO] Burning captions into final_subbed.mp4")
            burn_in_subtitles(final_fixed, subs_path, final_subbed)
            final_out = final_subbed
        else:
            log("[INFO] Overlay OFF: captions file created but not burned")

    log(f"[INFO] ✅ Done: {final_out}")
    return final_out, subs_written


# =============================================================================
# GUI
# =============================================================================

class App(tk.Tk):
    def __init__(self, project_root: Path):
        super().__init__()
        self.title("Videer GUI (WSL) — Text → Pexels → Voice → Video")
        self.geometry("1040x760")
        self.project_root = project_root

        self.preset = tk.StringVar(value="Fast YouTube Shorts")

        self.text_path = tk.StringVar(value=str(project_root / "inputs" / "narration.txt"))
        # description will be a multi-line Text widget; store None until created
        self.description = None
        self.out_video = tk.StringVar(value=str(project_root / "outputs" / "final.mp4"))
        self.workdir = tk.StringVar(value=str(project_root / "work"))

        self.voice = tk.StringVar(value=DEFAULT_VOICE)
        self.rate = tk.StringVar(value="+12%")
        self.aspect = tk.StringVar(value="9:16")
        self.query_strategy = tk.StringVar(value="topic_mapped")

        self.max_chars = tk.IntVar(value=320)

        self.add_subtitles = tk.BooleanVar(value=True)
        self.subtitle_style = tk.StringVar(value="pop_ass")
        self.overlay_text = tk.BooleanVar(value=True)
        self.font_color_name = tk.StringVar(value="Turquoise (default)")

        self._build_ui()
        self._apply_preset()

    def _log(self, msg: str) -> None:
        self.log_text.insert("end", msg + ("\n" if not msg.endswith("\n") else ""))
        self.log_text.see("end")
        self.update_idletasks()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=12, pady=12)

        preset_box = ttk.LabelFrame(root, text="Preset")
        preset_box.pack(fill="x", **pad)
        ttk.Label(preset_box, text="Preset:").pack(side="left", padx=8, pady=8)
        ttk.Combobox(preset_box, textvariable=self.preset, values=list(PRESETS.keys()),
                     state="readonly", width=28).pack(side="left", padx=8, pady=8)
        ttk.Button(preset_box, text="Apply", command=self._apply_preset).pack(side="left", padx=8, pady=8)

        files_box = ttk.LabelFrame(root, text="Files")
        files_box.pack(fill="x", **pad)

        ttk.Label(files_box, text="Narration text file:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(files_box, textvariable=self.text_path, width=92).grid(row=0, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(files_box, text="Browse", command=self._browse_text).grid(row=0, column=2, padx=8, pady=6)

        ttk.Label(files_box, text="Description (optional):").grid(row=1, column=0, sticky="nw", padx=8, pady=6)
        # multi-line description box with placeholder and clear button
        self.description_text = tk.Text(files_box, height=8, width=80, wrap="word")
        self.description_text.grid(row=1, column=1, sticky="we", padx=8, pady=6)

        right_col = ttk.Frame(files_box)
        right_col.grid(row=1, column=2, sticky="nw", padx=8, pady=6)
        ttk.Label(right_col, text="(If filled, this text will be used instead of the file.)", foreground="gray").pack(anchor="nw")
        ttk.Button(right_col, text="Clear", command=self._clear_description).pack(anchor="nw", pady=(6, 0))

        # placeholder text handling
        self._desc_placeholder = "Optional description (multiple sentences). If present, it will override the narration file."
        self.description_text.tag_configure("placeholder", foreground="gray")
        self._ensure_placeholder()
        self.description_text.bind("<FocusIn>", lambda e: self._clear_placeholder())
        self.description_text.bind("<FocusOut>", lambda e: self._ensure_placeholder())

        ttk.Label(files_box, text="Output video (name ignored):").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(files_box, textvariable=self.out_video, width=92).grid(row=2, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(files_box, text="Browse", command=self._browse_out).grid(row=2, column=2, padx=8, pady=6)

        ttk.Label(files_box, text="Workdir (cache):").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(files_box, textvariable=self.workdir, width=92).grid(row=3, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(files_box, text="Browse", command=self._browse_workdir).grid(row=3, column=2, padx=8, pady=6)

        ttk.Label(
            files_box,
            text="Cache folders: workdir/media · workdir/audio · workdir/segments · workdir/final_video.mp4 · workdir/final_audio.m4a",
            foreground="gray"
        ).grid(row=3, column=1, sticky="w", padx=8, pady=(0, 6))

        files_box.columnconfigure(1, weight=1)

        opts_box = ttk.LabelFrame(root, text="Voice + Video Options")
        opts_box.pack(fill="x", **pad)

        ttk.Label(opts_box, text="Aspect:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Combobox(opts_box, textvariable=self.aspect, values=["9:16", "16:9"],
                     state="readonly", width=8).grid(row=0, column=1, sticky="w", padx=8, pady=6)

        ttk.Label(opts_box, text="Voice:").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        ttk.Entry(opts_box, textvariable=self.voice, width=28).grid(row=0, column=3, sticky="w", padx=8, pady=6)

        ttk.Label(opts_box, text="Rate:").grid(row=0, column=4, sticky="w", padx=8, pady=6)
        ttk.Entry(opts_box, textvariable=self.rate, width=8).grid(row=0, column=5, sticky="w", padx=8, pady=6)

        ttk.Label(opts_box, text="Max chars/sentence:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(opts_box, textvariable=self.max_chars, width=8).grid(row=1, column=1, sticky="w", padx=8, pady=6)

        ttk.Label(opts_box, text="Query strategy:").grid(row=1, column=2, sticky="w", padx=8, pady=6)
        ttk.Combobox(opts_box, textvariable=self.query_strategy, values=["basic", "topic_mapped"],
                     state="readonly", width=14).grid(row=1, column=3, sticky="w", padx=8, pady=6)

        caps_box = ttk.LabelFrame(root, text="Text Overlay (Captions)")
        caps_box.pack(fill="x", **pad)

        ttk.Checkbutton(caps_box, text="Generate captions file", variable=self.add_subtitles)\
            .pack(side="left", padx=10, pady=8)

        ttk.Checkbutton(caps_box, text="Text overlay (burn into video)", variable=self.overlay_text)\
            .pack(side="left", padx=10, pady=8)

        ttk.Label(caps_box, text="Font color:").pack(side="left", padx=(20, 6), pady=8)
        ttk.Combobox(caps_box, textvariable=self.font_color_name, values=list(FONT_COLORS_ASS.keys()),
                     state="readonly", width=20).pack(side="left", padx=6, pady=8)

        ctrl = ttk.Frame(root)
        ctrl.pack(fill="x", **pad)
        ttk.Button(ctrl, text="Build Video", command=self._build).pack(side="left", padx=8, pady=8)
        ttk.Button(ctrl, text="Open outputs folder", command=self._open_outputs).pack(side="left", padx=8, pady=8)
        ttk.Button(ctrl, text="Clear cache (audio+segments)", command=self._clear_cache).pack(side="left", padx=8, pady=8)
        ttk.Button(ctrl, text="Clean old cache", command=self._clean_old_cache).pack(side="left", padx=8, pady=8)
        ttk.Button(ctrl, text="Check API key", command=self._check_api_key).pack(side="left", padx=8, pady=8)

        log_box = ttk.LabelFrame(root, text="Log")
        log_box.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(log_box, wrap="word", height=18)
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self._log("Ready.")

    def _apply_preset(self) -> None:
        p = PRESETS[self.preset.get()]
        self.aspect.set(str(p["aspect"]))
        self.max_chars.set(int(p["max_chars"]))
        self.rate.set(str(p["rate"]))
        self.query_strategy.set(str(p["query_strategy"]))
        self.add_subtitles.set(bool(p["add_subtitles"]))
        self.overlay_text.set(bool(p["overlay_text"]))
        self.font_color_name.set(str(p["font_color"]))
        # optional description override in presets (handled via multi-line box)
        # populate multi-line description if present in preset
        if hasattr(self, "description_text") and isinstance(self.description_text, tk.Text):
            self.description_text.delete("1.0", "end")
            val = str(p.get("description", ""))
            if val:
                self.description_text.insert("1.0", val)
            else:
                # restore placeholder if preset has no description
                self._ensure_placeholder()
        self._log(f"Applied preset: {self.preset.get()}")

    def _clear_description(self) -> None:
        if hasattr(self, "description_text") and isinstance(self.description_text, tk.Text):
            self.description_text.delete("1.0", "end")
            self._ensure_placeholder()

    def _clear_placeholder(self) -> None:
        if not hasattr(self, "description_text"):
            return
        t = self.description_text
        cur = t.get("1.0", "end").strip()
        if cur == self._desc_placeholder:
            t.delete("1.0", "end")
            t.tag_remove("placeholder", "1.0", "end")

    def _ensure_placeholder(self) -> None:
        if not hasattr(self, "description_text"):
            return
        t = self.description_text
        cur = t.get("1.0", "end").strip()
        if not cur:
            t.delete("1.0", "end")
            t.insert("1.0", self._desc_placeholder)
            t.tag_add("placeholder", "1.0", "end")

    def _browse_text(self) -> None:
        fp = filedialog.askopenfilename(
            initialdir=str(self.project_root),
            title="Select narration text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if fp:
            self.text_path.set(fp)

    def _browse_out(self) -> None:
        fp = filedialog.asksaveasfilename(
            initialdir=str(self.project_root / "outputs"),
            title="Select output mp4 (name ignored)",
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4"), ("All files", "*.*")],
        )
        if fp:
            self.out_video.set(fp)

    def _browse_workdir(self) -> None:
        dp = filedialog.askdirectory(initialdir=str(self.project_root), title="Select work directory")
        if dp:
            self.workdir.set(dp)

    def _open_outputs(self) -> None:
        out_dir = (self.project_root / "outputs").resolve()
        subprocess.run(["bash", "-lc", f"explorer.exe '{out_dir.as_posix()}'"], check=False)

    def _clear_cache(self) -> None:
        w = Path(self.workdir.get()).expanduser().resolve()
        for sub in ("audio", "segments"):
            p = w / sub
            if p.exists():
                for item in p.glob("*"):
                    try:
                        if item.is_file():
                            item.unlink()
                    except Exception:
                        pass
        for p in (w / "final_video.mp4", w / "final_audio.m4a"):
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        self._log("Cleared cache: work/audio + work/segments + work/final_video.mp4 + work/final_audio.m4a")

    def _clean_old_cache(self) -> None:
        days = simpledialog.askinteger("Clean old cache", "Remove files older than how many days?", initialvalue=30, minvalue=1, maxvalue=3650)
        if not days:
            return
        w = Path(self.workdir.get()).expanduser().resolve()
        removed = clean_old_work(w, days, log=self._log)
        self._log(f"Cleaned {removed} files older than {days} days from {w}")

    def _check_api_key(self) -> None:
        try:
            key = get_pexels_api_key(self.project_root)
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": key},
                params={"query": "mountains", "per_page": 1},
                timeout=20,
            )
            self._log(f"API key check: status={r.status_code}")
            if r.status_code == 200:
                messagebox.showinfo("API Key OK", "PEXELS_API_KEY works (status 200).")
            else:
                messagebox.showerror("API Key Failed", f"Status: {r.status_code}\n{r.text[:200]}")
        except Exception as e:
            self._log(f"API key check failed: {e}")
            messagebox.showerror("API Key Failed", str(e))

    def _build(self) -> None:
        try:
            text_path = Path(self.text_path.get()).expanduser()
            out_video = Path(self.out_video.get()).expanduser()
            workdir = Path(self.workdir.get()).expanduser()

            if not text_path.exists():
                messagebox.showerror("Missing file", f"Text file not found:\n{text_path}")
                return

            # read optional override from multi-line description widget (if present)
            desc_override = None
            if hasattr(self, "description_text") and isinstance(self.description_text, tk.Text):
                raw = self.description_text.get("1.0", "end").strip()
                # treat placeholder as empty
                if raw and raw != getattr(self, "_desc_placeholder", ""):
                    desc_override = raw

            opts = BuildOptions(
                text_path=text_path,
                text_override=desc_override,
                out_video=out_video,
                workdir=workdir,
                max_chars=int(self.max_chars.get()),
                voice=self.voice.get().strip() or DEFAULT_VOICE,
                rate=self.rate.get().strip() or "+0%",
                aspect=self.aspect.get().strip(),          # type: ignore[arg-type]
                query_strategy=self.query_strategy.get().strip(),  # type: ignore[arg-type]
                add_subtitles=bool(self.add_subtitles.get()),
                subtitle_style="pop_ass",
                overlay_text=bool(self.overlay_text.get()),
                font_color_name=self.font_color_name.get().strip(),
            )

            self._log("\n=== Starting build ===")
            final_out, subs = build_video(self.project_root, opts, log=self._log)

            self._log(f"\nOutput video: {final_out}")
            if subs:
                self._log(f"Captions file: {subs}")

            messagebox.showinfo("Done", f"Video created:\n{final_out}")

        except Exception as e:
            self._log(f"\nERROR: {e}")
            messagebox.showerror("Error", str(e))


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app = App(project_root=project_root)
    app.mainloop()


if __name__ == "__main__":
    main()
