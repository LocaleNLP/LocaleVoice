"""Null TTS provider: speech explicitly unavailable (Milestone 6A).

Used until a real provider is verified for Darija (see docs/16).
Never raises anything but TTSError with a user-safe message.
"""

from __future__ import annotations

from localevoice.providers.tts.base import TTSProvider, TTSEpisode, TTSError

UNAVAILABLE_MESSAGE = (
    "Speech generation is not available yet — no voice provider has "
    "been set up. You can read the full answer above."
)


class NullTTSProvider(TTSProvider):
    """Placeholder that always reports speech as unavailable."""

    name: str = "null"

    def is_available(self) -> bool:
        return False

    def synthesize(
        self, text: str, *, voice: str | None = None, timeout: float = 60.0
    ) -> TTSEpisode:
        raise TTSError(UNAVAILABLE_MESSAGE)
