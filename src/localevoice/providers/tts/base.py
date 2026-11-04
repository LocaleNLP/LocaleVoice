"""TTS provider contract (Milestone 6A).

LocaleVoice speaks only final, approved answer text. No Meta TTS
endpoint exists (Voice Transcribe is speech-to-text), and no third
party has been verified yet (see docs/16), so the default provider
is NullTTSProvider, which reports speech as unavailable. Real
providers plug in behind this interface without touching callers.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

_CITATION = re.compile(r"\[[A-Za-z0-9][A-Za-z0-9._-]*\]")
_WHITESPACE = re.compile(r"\s+")


class TTSError(Exception):
    """Speech generation failed or is unavailable (user-safe message)."""


@dataclass(frozen=True)
class TTSEpisode:
    audio_bytes: bytes
    mime_type: str  # e.g. "audio/wav", "audio/mpeg"
    voice_name: str
    provider_name: str


def speech_text_for(answer_text: str) -> str:
    """Clean answer text for speech: strip [citation-ids], collapse space.

    Citations, document IDs, and diagnostics must never be spoken.
    Returns "" when nothing speakable remains.
    """
    cleaned = _CITATION.sub("", answer_text or "")
    return _WHITESPACE.sub(" ", cleaned).strip()


class TTSProvider(ABC):
    """Vendor-neutral speech synthesis interface."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """True when synthesis can be attempted (keys, config present)."""

    @abstractmethod
    def synthesize(
        self, text: str, *, voice: str | None = None, timeout: float = 60.0
    ) -> TTSEpisode:
        """Synthesize already-cleaned text; raise TTSError on failure."""
