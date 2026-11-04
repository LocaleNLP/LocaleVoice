"""Unit tests for the TTS provider contract. No network, no audio.

Providers are fakes: these prove the interface rules (text cleaning,
selection, failure semantics), not any vendor's voice quality.
"""

from __future__ import annotations

import pytest

from localevoice.providers.tts import (
    NullTTSProvider,
    TTSError,
    TTSEpisode,
    get_tts_provider,
    speech_text_for,
)
from localevoice.providers.tts.base import TTSProvider


class _FakeProvider(TTSProvider):
    name = "fake"

    def __init__(self):
        self.calls: list[str] = []

    def is_available(self) -> bool:
        return True

    def synthesize(self, text, *, voice=None, timeout=60.0):
        self.calls.append(text)
        return TTSEpisode(
            audio_bytes=b"RIFFfake",
            mime_type="audio/wav",
            voice_name=voice or "fake-voice",
            provider_name="fake",
        )


def test_speech_text_strips_citations_and_collapses_space():
    assert (
        speech_text_for("القمح مزيان. [feedipedia-wheat-grain]  نعم")
        == "القمح مزيان. نعم"
    )
    assert speech_text_for("[a]  [b]") == ""
    assert speech_text_for("") == ""


def test_speech_text_keeps_arabic_script():
    text = "وعليكم السلام! مرحبا بك."
    assert speech_text_for(text) == text


def test_null_provider_unavailable_with_safe_message():
    provider = NullTTSProvider()
    assert provider.is_available() is False
    with pytest.raises(TTSError, match="not available"):
        provider.synthesize("hello")


def test_factory_defaults_to_null(monkeypatch):
    monkeypatch.delenv("LOCALEVOICE_TTS_PROVIDER", raising=False)
    assert isinstance(get_tts_provider(), NullTTSProvider)


def test_factory_rejects_unknown_provider():
    with pytest.raises(TTSError, match="Unknown TTS provider"):
        get_tts_provider("definitely-not-real")


def test_fake_provider_receives_cleaned_text_only():
    provider = _FakeProvider()
    episode = provider.synthesize(
        speech_text_for("Answer here. [feedipedia-wheat-grain]")
    )
    assert provider.calls == ["Answer here."]
    assert episode.audio_bytes.startswith(b"RIFF")
    assert "feedipedia" not in provider.calls[0]
