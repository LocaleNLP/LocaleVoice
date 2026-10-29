"""Meta Muse Voice Transcribe file provider (Milestone 1 smoke-test primitive).

Uploads a WAV file to the documented multipart endpoint. Hosted inference
only; no local models.
"""

from __future__ import annotations

import json
import os

import requests

ASR_URL = "https://api.meta.ai/v1/asr/transcribe"
ASR_MODE = "PUSH_TO_TALK"
ASR_ENCODING = "WAV"


class MetaASRError(Exception):
    """Raised when transcription input validation or the ASR request fails."""


def _redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        if secret and secret in text:
            text = text.replace(secret, "***REDACTED***")
    return text


def _build_request_part(model_id: str, language_bias: str | None) -> str:
    part: dict[str, str] = {
        "model": model_id,
        "mode": ASR_MODE,
        "audioEncoding": ASR_ENCODING,
    }
    # Optional recognizer hint only. Arabic bias is NOT presented as
    # guaranteed Moroccan Darija recognition (see docs/02).
    if language_bias:
        part["language"] = language_bias
    return json.dumps(part)


def _extract_transcript(payload: object, key: str) -> str:
    """Pull transcript text from the decoded ASR JSON payload.

    Accepts the documented text field plus adjacent common shapes so a real
    response is not rejected over a field-name variant; anything without
    usable text is an error, never an empty success.
    """
    candidates: list[str] = []
    if isinstance(payload, dict):
        for field in ("text", "transcript", "transcription"):
            value = payload.get(field)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())
        for list_field in ("results", "turns"):
            items = payload.get(list_field)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        for field in ("text", "transcript", "transcription"):
                            value = item.get(field)
                            if isinstance(value, str) and value.strip():
                                candidates.append(value.strip())
    if not candidates:
        raise MetaASRError(
            _redact(
                f"ASR response contained no usable transcript text: {payload!r}",
                [key],
            )
        )
    return candidates[0]


def transcribe_file(
    path: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    language_bias: str | None = None,
    timeout: float = 120.0,
) -> str:
    """Transcribe a WAV file via Meta Muse Voice Transcribe; return the text.

    Args:
        path: Filesystem path to a `.wav` file.
        api_key: Override for `MODEL_API_KEY`.
        model: Override for `META_ASR_MODEL`.
        language_bias: Optional recognizer hint (e.g. ``"ar"``). Falls back
            to `LOCALEVOICE_ASR_LANGUAGE_BIAS` when not given. This is a
            hint, not a guarantee of Darija support.
        timeout: HTTP timeout in seconds.

    Raises:
        FileNotFoundError: if the path does not exist or is not a file.
        ValueError: if the path is not a WAV file.
        MetaASRError: on missing configuration, request failure, or a
            response with no usable transcript text.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    if not path.lower().endswith(".wav"):
        raise ValueError(f"Only WAV files are supported, got: {path}")

    key = api_key if api_key is not None else os.environ.get("MODEL_API_KEY")
    if not key:
        raise MetaASRError(
            "Missing API key: set the MODEL_API_KEY environment variable."
        )
    model_id = model if model is not None else os.environ.get("META_ASR_MODEL")
    if not model_id:
        raise MetaASRError("Missing model identifier: set META_ASR_MODEL.")
    if language_bias is None:
        language_bias = os.environ.get("LOCALEVOICE_ASR_LANGUAGE_BIAS") or None

    request_part = _build_request_part(model_id, language_bias)
    try:
        with open(path, "rb") as audio:
            response = requests.post(
                ASR_URL,
                headers={"Authorization": f"Bearer {key}"},
                data={"request": request_part},
                files={"audio": (os.path.basename(path), audio, "audio/wav")},
                timeout=timeout,
            )
    except requests.RequestException as exc:
        raise MetaASRError(
            _redact(f"ASR request failed: {exc}", [key])
        ) from exc

    if response.status_code >= 400:
        detail = _redact(response.text[:1000], [key])
        raise MetaASRError(
            f"ASR request failed with status {response.status_code}: {detail}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        detail = _redact(response.text[:1000], [key])
        raise MetaASRError(
            f"ASR response was not valid JSON (status "
            f"{response.status_code}): {detail}"
        ) from exc

    return _extract_transcript(payload, key)
