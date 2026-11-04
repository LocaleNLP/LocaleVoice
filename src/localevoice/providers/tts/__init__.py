"""TTS provider selection (Milestone 6A).

`LOCALEVOICE_TTS_PROVIDER` names the backend (default: "null").
Unknown names fail closed to a TTSError so a typo never silently
disables speech or, worse, routes text somewhere unexpected.
"""

from __future__ import annotations

import os

from localevoice.providers.tts.base import (
    TTSProvider,
    TTSError,
    TTSEpisode,
    speech_text_for,
)
from localevoice.providers.tts.null import UNAVAILABLE_MESSAGE, NullTTSProvider


def get_tts_provider(name: str | None = None) -> TTSProvider:
    """Return the configured TTS backend (default: null/unavailable)."""
    selected = (name or os.environ.get("LOCALEVOICE_TTS_PROVIDER") or "null").strip().lower()
    if selected == "null":
        return NullTTSProvider()
    raise TTSError(
        f"Unknown TTS provider {selected!r}. No voice provider has been "
        "verified yet; unset LOCALEVOICE_TTS_PROVIDER to use the null "
        "backend."
    )


__all__ = [
    "NullTTSProvider",
    "TTSProvider",
    "TTSError",
    "TTSEpisode",
    "UNAVAILABLE_MESSAGE",
    "get_tts_provider",
    "speech_text_for",
]
