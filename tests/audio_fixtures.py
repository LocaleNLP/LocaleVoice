"""Real (synthetic-tone) audio fixtures for tests. No network, no speech.

Tones verify plumbing only: normalization, validation, cleanup, and UI
flow. They prove nothing about transcription quality or Darija.
"""

from __future__ import annotations

import io
import math
import shutil
import struct
import subprocess
import wave

import pytest


def make_wav_bytes(
    rate: int = 24000,
    channels: int = 1,
    seconds: float = 0.1,
    width: int = 2,
    freq: float = 440.0,
) -> bytes:
    """Build a minimal PCM WAV tone in memory."""
    n = max(1, int(rate * seconds))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(rate)
        for i in range(n):
            value = int(8000 * math.sin(2 * math.pi * freq * i / rate))
            wav.writeframes(struct.pack("<h", value) * channels)
    return buf.getvalue()


def make_converted_bytes(kind: str) -> bytes:
    """Build a 0.2s tone in a compressed container via ffmpeg.

    Skips the calling test when ffmpeg is unavailable. Uses a
    seekable temp file (mp4/webm muxers need it) and encoder-safe
    rates (opus requires 48/24/16/12/8 kHz).
    """
    import os
    import tempfile

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not installed")
    rate = "48000" if kind == "webm" else "44100"
    fd, path = tempfile.mkstemp(suffix="." + kind)
    os.close(fd)
    try:
        proc = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2",
                "-ar", rate, "-ac", "2", path,
            ],
            capture_output=True,
            timeout=60,
        )
        assert proc.returncode == 0, proc.stderr.decode()[-300:]
        with open(path, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
