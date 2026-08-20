"""
video_converter.py — Convert OpenCV-written MP4 files to browser-compatible
H.264 + yuv420p + faststart using the bundled ffmpeg from imageio-ffmpeg.

This fixes the critical bug where moov atom is at end-of-file, causing
browsers to show a black player at 0:00 because they cannot play before
downloading the entire 77MB file.
"""
from __future__ import annotations
import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

_FFMPEG_PATH: Optional[str] = None


def get_ffmpeg() -> Optional[str]:
    """Return path to ffmpeg binary, trying imageio_ffmpeg first, then PATH."""
    global _FFMPEG_PATH
    if _FFMPEG_PATH:
        return _FFMPEG_PATH
    # 1. imageio_ffmpeg (bundled, always available after pip install)
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p):
            _FFMPEG_PATH = p
            return p
    except Exception:
        pass
    # 2. System PATH
    import shutil
    p = shutil.which("ffmpeg")
    if p:
        _FFMPEG_PATH = p
        return p
    return None


def convert_to_web_h264(input_path: str, output_path: str) -> bool:
    """
    Convert input video to browser-compatible H.264 MP4 with faststart.

    Settings:
      - H.264 video codec (libx264)
      - yuv420p pixel format (universal browser support)
      - CRF 23 (good quality, ~6-8 MB for a 15s 1080p clip)
      - preset ultrafast (low CPU, fast encode)
      - +faststart (moov atom at beginning for instant streaming)
      - Audio copy if present, else no audio

    Returns True on success, False on failure.
    """
    ffmpeg = get_ffmpeg()
    if not ffmpeg:
        logger.warning("ffmpeg not available — cannot convert video for browser playback")
        return False

    tmp_output = output_path + ".tmp.mp4"
    cmd = [
        ffmpeg,
        "-y",                       # overwrite
        "-i", input_path,           # input
        "-c:v", "libx264",          # H.264 encoder
        "-pix_fmt", "yuv420p",      # universal pixel format
        "-crf", "23",               # quality (lower = better, 18-28 normal)
        "-preset", "ultrafast",     # speed over compression
        "-movflags", "+faststart",  # put moov atom at beginning
        "-an",                      # no audio (running videos rarely have audio)
        tmp_output,
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace")[-500:]
            logger.error(f"ffmpeg conversion failed for {input_path}:\n{err}")
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            return False

        # Atomic replace
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(tmp_output, output_path)
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        logger.info(f"Converted {input_path} -> {output_path} ({size_mb:.1f} MB)")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg timed out for {input_path}")
        if os.path.exists(tmp_output):
            os.remove(tmp_output)
        return False
    except Exception as e:
        logger.error(f"ffmpeg exception: {e}")
        if os.path.exists(tmp_output):
            os.remove(tmp_output)
        return False


def is_web_compatible(path: str) -> bool:
    """
    Check if a video file has moov atom near the beginning (within first 1MB).
    This is the proxy for 'browser can start playing immediately'.
    """
    if not os.path.exists(path):
        return False
    try:
        with open(path, "rb") as f:
            # Read first 1MB looking for 'moov' before 'mdat'
            chunk = f.read(1024 * 1024)
        moov_pos = chunk.find(b"moov")
        mdat_pos = chunk.find(b"mdat")
        # moov must exist and appear before mdat
        if moov_pos >= 0 and (mdat_pos < 0 or moov_pos < mdat_pos):
            return True
        return False
    except Exception:
        return False


def ensure_web_compatible(raw_path: str, output_path: str) -> str:
    """
    If output_path already exists and is web-compatible, return it.
    If not, convert raw_path -> output_path using ffmpeg.
    Returns the final path (output_path on success, raw_path as fallback).
    """
    if is_web_compatible(output_path):
        return output_path
    logger.info(f"Converting {raw_path} to browser-compatible H.264+faststart...")
    ok = convert_to_web_h264(raw_path, output_path)
    if ok:
        return output_path
    logger.warning(f"ffmpeg conversion failed — falling back to original: {raw_path}")
    return raw_path
