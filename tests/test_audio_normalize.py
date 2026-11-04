"""Unit tests for audio inspection/normalization. No network, no speech.

Tones verify plumbing only (formats, conversion, limits, cleanup).
Compressed-format tests skip cleanly when ffmpeg is unavailable.
"""

from __future__ import annotations

import os

import pytest

from audio_fixtures import make_converted_bytes, make_wav_bytes
from localevoice.audio.normalize import (
    TARGET_SAMPLE_RATE,
    AudioValidationError,
    NormalizedAudio,
    ffmpeg_available,
    is_asr_conforming,
    read_wav_format,
    sniff_container,
)

needs_ffmpeg = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg not installed"
)


def test_sniff_detects_containers_from_bytes():
    assert sniff_container(make_wav_bytes()) == "wav"
    assert sniff_container(b"ID3\x04\x00" + b"\x00" * 20) == "mp3"
    assert sniff_container(b"\xff\xfb\x90\x00" + b"\x00" * 20) == "mp3"
    assert sniff_container(b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 20) == "m4a"
    assert sniff_container(b"\x1a\x45\xdf\xa3" + b"\x00" * 20) == "webm"
    assert sniff_container(b"OggS" + b"\x00" * 20) == "ogg"
    assert sniff_container(b"x" * 100) == "unknown"


def test_conforming_wav_passes_through_byte_identical(tmp_path):
    data = make_wav_bytes(rate=24000, channels=1)
    with NormalizedAudio(data, "q.wav") as norm:
        assert norm.converted is False
        assert norm.final.sample_rate == 24000
        assert norm.final.channels == 1
        assert open(norm.path, "rb").read() == data
    assert not os.path.exists(norm.path)


def test_conforming_16khz_wav_passes_through():
    data = make_wav_bytes(rate=16000, channels=1)
    with NormalizedAudio(data, "q.wav") as norm:
        assert norm.converted is False
        assert is_asr_conforming(norm.final) is True


@needs_ffmpeg
def test_stereo_wav_converts_to_mono():
    data = make_wav_bytes(rate=44100, channels=2, seconds=0.2)
    with NormalizedAudio(data, "q.wav") as norm:
        assert norm.converted is True
        assert norm.original.channels == 2
        assert norm.original.sample_rate == 44100
        assert is_asr_conforming(norm.final) is True
        assert norm.final.sample_rate == TARGET_SAMPLE_RATE


@needs_ffmpeg
def test_wrong_sample_rate_converts():
    data = make_wav_bytes(rate=48000, channels=1, seconds=0.2)
    with NormalizedAudio(data, "q.wav") as norm:
        assert norm.converted is True
        assert norm.final.sample_rate == TARGET_SAMPLE_RATE
        assert is_asr_conforming(norm.final) is True


@needs_ffmpeg
@pytest.mark.parametrize(
    "kind,ext", [("mp3", ".mp3"), ("mp4", ".m4a"), ("webm", ".webm")]
)
def test_compressed_containers_convert(kind, ext):
    data = make_converted_bytes(kind)
    with NormalizedAudio(data, "q" + ext) as norm:
        assert norm.converted is True
        assert is_asr_conforming(norm.final) is True
        assert 0 < norm.final.duration_s <= 1.0


def test_corrupt_wav_rejected():
    with pytest.raises(AudioValidationError, match="corrupted"):
        NormalizedAudio(b"RIFF\x00\x00\x00\x00WAVEjunk", "q.wav")


def test_garbage_after_magic_rejected_as_corrupt():
    # Magic-valid header with a nonsense body: wave raises bare
    # RuntimeError here, which must still map to AudioValidationError.
    with pytest.raises(AudioValidationError, match="corrupted"):
        NormalizedAudio(b"RIFF\xff\x00\x00\x00WAVE" + b"junk" * 30, "q.wav")


def test_empty_input_rejected():
    with pytest.raises(AudioValidationError, match="No audio"):
        NormalizedAudio(b"", "q.wav")


def test_unrecognized_bytes_rejected():
    with pytest.raises(AudioValidationError, match="not a recognized audio"):
        NormalizedAudio(b"x" * 100, "q.wav")


def test_unsupported_extension_rejected():
    with pytest.raises(AudioValidationError, match="Unsupported audio format"):
        NormalizedAudio(make_wav_bytes(), "q.ogg")
    with pytest.raises(AudioValidationError, match="Unsupported audio format"):
        NormalizedAudio(make_wav_bytes(), "q.txt")


def test_oversize_rejected_without_temp_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "localevoice.audio.normalize.tempfile.mkdtemp",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no temp dir")),
    )
    big = make_wav_bytes(seconds=0.1)
    with pytest.raises(AudioValidationError, match="too large"):
        NormalizedAudio(big, "q.wav", max_bytes=10)


def test_too_long_rejected_and_cleaned():
    data = make_wav_bytes(seconds=0.5)
    with pytest.raises(AudioValidationError, match="too long"):
        NormalizedAudio(data, "q.wav", max_duration_s=0.1)


def test_no_ffmpeg_fallback_rejects_conversion(monkeypatch):
    monkeypatch.setattr(
        "localevoice.audio.normalize.ffmpeg_available", lambda: False
    )
    with pytest.raises(AudioValidationError, match="FFmpeg is not"):
        NormalizedAudio(make_wav_bytes(rate=48000), "q.wav")
    # Conforming input still works without ffmpeg.
    with NormalizedAudio(make_wav_bytes(), "q.wav") as norm:
        assert norm.converted is False


def test_temp_files_cleaned_on_success_and_failure():
    data = make_wav_bytes()
    with NormalizedAudio(data, "q.wav") as norm:
        path = norm.path
        assert os.path.exists(path)
    assert not os.path.exists(path)
    assert not os.path.exists(os.path.dirname(path))


def test_truncated_wav_rejected():
    full = make_wav_bytes(seconds=0.5)
    truncated = full[: len(full) // 2]
    assert sniff_container(truncated) == "wav"
    with pytest.raises(AudioValidationError, match="truncated"):
        NormalizedAudio(truncated, "q.wav")


@needs_ffmpeg
def test_misleading_extension_trusts_bytes():
    mp3 = make_converted_bytes("mp3")
    with NormalizedAudio(mp3, "q.wav") as norm:
        assert norm.original.container == "mp3"
        assert norm.converted is True
        assert is_asr_conforming(norm.final) is True


@needs_ffmpeg
def test_failed_conversion_cleans_temp_dir(monkeypatch):
    import tempfile

    created: list[str] = []
    real_mkdtemp = tempfile.mkdtemp

    def _tracking(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(
        "localevoice.audio.normalize.tempfile.mkdtemp", _tracking
    )
    garbage_mp3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 500
    with pytest.raises(AudioValidationError, match="Could not convert"):
        NormalizedAudio(garbage_mp3, "q.mp3")
    assert created, "expected a temp dir to have been created"
    for path in created:
        assert not os.path.exists(path)


def test_conversion_timeout_mapped_and_cleaned(monkeypatch):
    import subprocess
    import tempfile

    created: list[str] = []
    real_mkdtemp = tempfile.mkdtemp

    def _tracking(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(
        "localevoice.audio.normalize.tempfile.mkdtemp", _tracking
    )

    def _hang(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=60.0)

    monkeypatch.setattr("localevoice.audio.normalize.subprocess.run", _hang)
    with pytest.raises(AudioValidationError, match="timed out"):
        NormalizedAudio(make_wav_bytes(rate=48000), "q.wav")
    for path in created:
        assert not os.path.exists(path)


def test_read_wav_format_reports_parameters(tmp_path):
    path = str(tmp_path / "a.wav")
    open(path, "wb").write(make_wav_bytes(rate=16000, seconds=0.25))
    fmt = read_wav_format(path)
    assert (fmt.container, fmt.sample_rate, fmt.channels) == ("wav", 16000, 1)
    assert fmt.duration_s == pytest.approx(0.25, abs=0.01)
