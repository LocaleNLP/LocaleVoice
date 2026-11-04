"""Audio inspection and normalization for ASR input."""

from localevoice.audio.normalize import (
    ASR_SAMPLE_RATES,
    MAX_DURATION_S,
    MAX_UPLOAD_BYTES,
    SUPPORTED_EXTENSIONS,
    TARGET_SAMPLE_RATE,
    AudioFormat,
    AudioValidationError,
    NormalizedAudio,
    ffmpeg_available,
    is_asr_conforming,
    read_wav_format,
    sniff_container,
)

__all__ = [
    "ASR_SAMPLE_RATES",
    "MAX_DURATION_S",
    "MAX_UPLOAD_BYTES",
    "SUPPORTED_EXTENSIONS",
    "TARGET_SAMPLE_RATE",
    "AudioFormat",
    "AudioValidationError",
    "NormalizedAudio",
    "ffmpeg_available",
    "is_asr_conforming",
    "read_wav_format",
    "sniff_container",
]
