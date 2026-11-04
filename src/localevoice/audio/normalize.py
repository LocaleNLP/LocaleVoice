"""Audio inspection and normalization for ASR (Milestone 6A).

Meta Muse Voice Transcribe accepts only mono s16le WAV at 16000 or
24000 Hz (verified empirically: anything else is an HTTP 400
"Unsupported WAV format"). Microphone recordings already conform
(Streamlit records 16 kHz WAV); user uploads often do not, so uploads
are inspected and, when needed, converted before any provider call.

Strategy: stdlib `wave` inspects and passes through conforming WAVs;
FFmpeg (when installed) converts everything else. Without FFmpeg,
only already-conforming WAVs are accepted and anything needing
conversion is rejected with an actionable message.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass

TARGET_SAMPLE_RATE = 24000
ASR_SAMPLE_RATES = (16000, 24000)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MiB input cap
MAX_DURATION_S = 120.0  # 2-minute question cap
FFMPEG_TIMEOUT_S = 60.0

SUPPORTED_EXTENSIONS = (".wav", ".mp3", ".m4a", ".webm")


class AudioValidationError(ValueError):
    """User-facing audio rejection (format, corruption, size, duration)."""


@dataclass(frozen=True)
class AudioFormat:
    container: str  # wav, mp3, m4a, webm, or unknown
    codec: str  # pcm_s16le, mp3, aac, opus, ... or unknown
    sample_rate: int  # Hz, 0 when unknown
    channels: int  # 0 when unknown
    sample_width: int  # bytes per sample, 0 when unknown
    frames: int  # 0 when unknown
    duration_s: float  # 0.0 when unknown
    size_bytes: int


def sniff_container(data: bytes) -> str:
    """Detect the audio container from magic bytes (never the filename)."""
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if len(data) >= 3 and (
        data[0:3] == b"ID3" or (data[0] == 0xFF and data[1] & 0xE0 == 0xE0)
    ):
        return "mp3"
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return "m4a"
    if len(data) >= 4 and data[0:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    if len(data) >= 4 and data[0:4] == b"OggS":
        return "ogg"
    return "unknown"


def read_wav_format(path: str, size_bytes: int = 0) -> AudioFormat:
    """Parse WAV parameters with the stdlib; reject corrupt files."""
    try:
        with wave.open(path, "rb") as wav:
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            rate = wav.getframerate()
            frames = wav.getnframes()
            codec = wav.getcomptype()
    except Exception as exc:  # noqa: BLE001 - untrusted bytes, fail closed
        # wave/chunk/struct raise an assortment (Error, EOFError,
        # RuntimeError, struct.error) on malformed input; every parse
        # failure means the file cannot be trusted.
        detail = str(exc) or type(exc).__name__
        raise AudioValidationError(
            "This WAV file is corrupted or uses an unsupported "
            f"encoding ({detail}). Try exporting it as a standard WAV."
        ) from exc
    if frames <= 0:
        raise AudioValidationError(
            "This recording is empty (no audio frames). Record or "
            "upload a question with speech in it."
        )
    try:
        size = size_bytes or os.path.getsize(path)
    except OSError:
        size = 0
    expected = 44 + frames * channels * width
    if size and size < expected:
        raise AudioValidationError(
            "This WAV file is truncated (its data is shorter than its "
            "header claims). Re-export or re-record it."
        )
    return AudioFormat(
        container="wav",
        codec="pcm_s16le" if (codec == "NONE" and width == 2) else codec,
        sample_rate=rate,
        channels=channels,
        sample_width=width,
        frames=frames,
        duration_s=frames / rate if rate else 0.0,
        size_bytes=size,
    )


def is_asr_conforming(fmt: AudioFormat) -> bool:
    """True when Meta accepts the audio as-is (mono s16le, 16/24 kHz)."""
    return (
        fmt.container == "wav"
        and fmt.codec == "pcm_s16le"
        and fmt.channels == 1
        and fmt.sample_width == 2
        and fmt.sample_rate in ASR_SAMPLE_RATES
    )


def ffmpeg_available() -> bool:
    """True when the ffmpeg binary is on PATH."""
    return shutil.which("ffmpeg") is not None


def _convert_with_ffmpeg(src: str, dst: str, max_duration_s: float) -> str:
    """Convert to mono s16le WAV; return stderr tail for diagnostics.

    Output is capped at max_duration_s + 5s so over-long input cannot
    expand conversion work or disk use without bound; the duration
    limit itself is enforced afterwards by the caller.
    """
    try:
        proc = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", src, "-ac", "1", "-ar", str(TARGET_SAMPLE_RATE),
                "-sample_fmt", "s16", "-t", f"{max_duration_s + 5:.0f}",
                "-f", "wav", dst,
            ],
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioValidationError(
            "Audio conversion timed out. Try a shorter recording."
        ) from exc
    if proc.returncode != 0:
        raise AudioValidationError(
            "Could not convert this audio file to a supported WAV. "
            "It may be corrupted or use an unsupported codec."
        )
    return (proc.stderr or "")[-500:]


class NormalizedAudio:
    """A validated, ASR-ready WAV file plus its format provenance.

    Use as a context manager (or call close()): backing temp files are
    always removed. `converted` is False when the input already
    conformed and was passed through byte-identical.
    """

    def __init__(
        self,
        data: bytes,
        filename: str,
        *,
        max_bytes: int = MAX_UPLOAD_BYTES,
        max_duration_s: float = MAX_DURATION_S,
    ) -> None:
        if not filename or data is None or len(data) == 0:
            raise AudioValidationError(
                "No audio received. Upload a recording and retry."
            )
        ext = os.path.splitext(filename.lower())[1]
        if ext not in SUPPORTED_EXTENSIONS:
            raise AudioValidationError(
                f"Unsupported audio format ({ext or 'no extension'}). "
                "Upload WAV, MP3, M4A, or WebM."
            )
        if len(data) > max_bytes:
            raise AudioValidationError(
                f"Recording is too large ({len(data) / 1024 / 1024:.1f} MiB). "
                f"Please keep it under {max_bytes / 1024 / 1024:.0f} MiB."
            )
        container = sniff_container(data)
        if container == "unknown":
            raise AudioValidationError(
                "This file is not a recognized audio recording. Upload "
                "WAV, MP3, M4A, or WebM."
            )
        if container == "ogg":
            raise AudioValidationError(
                "OGG audio is not supported. Upload WAV, MP3, M4A, or WebM."
            )

        self._tmpdir = tempfile.mkdtemp(prefix="localevoice-audio-")
        self._closed = False
        try:
            self._prepare(data, ext, container, max_duration_s)
        except BaseException:
            # __init__ failed: the caller never gets an object to
            # close, so clean up here on every failure path.
            self.close()
            raise

    def _prepare(
        self, data: bytes, ext: str, container: str, max_duration_s: float
    ) -> None:
        src = os.path.join(self._tmpdir, "input" + ext)
        with open(src, "wb") as fh:
            fh.write(data)

        if container == "wav":
            original = read_wav_format(src, len(data))
        else:
            # Compressed input: container is known from magic bytes;
            # precise codec/rate come from the converter, not the name.
            original = AudioFormat(
                container=container,
                codec="unknown",
                sample_rate=0,
                channels=0,
                sample_width=0,
                frames=0,
                duration_s=0.0,
                size_bytes=len(data),
            )
        self.original = original

        if is_asr_conforming(original):
            self.path = src
            self.final = original
            self.converted = False
        else:
            if not ffmpeg_available():
                raise AudioValidationError(
                    "This audio needs conversion (Meta requires mono "
                    "16-bit audio at 16 or 24 kHz) but FFmpeg is not "
                    "installed. Install FFmpeg or re-export the file."
                )
            dst = os.path.join(self._tmpdir, "asr-ready.wav")
            self.ffmpeg_log = _convert_with_ffmpeg(src, dst, max_duration_s)
            final = read_wav_format(dst)
            self.path = dst
            self.final = final
            self.converted = True

        if self.final.duration_s > max_duration_s:
            raise AudioValidationError(
                f"Recording is too long ({self.final.duration_s:.0f}s). "
                f"Please keep questions under {max_duration_s:.0f} seconds."
            )

    ffmpeg_log: str = ""

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def __enter__(self) -> "NormalizedAudio":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
