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
    """Transcription failure with a machine-readable category.

    `category` is one of: invalid_audio, no_speech, too_large, auth,
    rate_limit, timeout, network, provider, bad_response, config.
    `status_code` and `session_id` (provider correlation id) are set
    when a response was received. Messages never contain secrets.
    """

    def __init__(
        self,
        message: str,
        *,
        category: str = "provider",
        status_code: int | None = None,
        session_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.status_code = status_code
        self.session_id = session_id


# User-facing guidance per category. Technical detail (status codes,
# session ids) stays in the expandable diagnostics section.
CATEGORY_MESSAGES = {
    "invalid_audio": (
        "This recording uses an audio format the transcriber rejects. "
        "Try a shorter WAV, MP3, M4A, or WebM recording."
    ),
    "no_speech": (
        "No speech was detected in this recording. Record your "
        "question again, speaking clearly."
    ),
    "too_large": (
        "This recording is too large or too long for transcription. "
        "Keep it under 10 MiB and 2 minutes."
    ),
    "auth": (
        "Transcription was refused (authentication). Check the API key "
        "configuration, then retry."
    ),
    "rate_limit": (
        "The transcriber is rate-limited right now. Wait a moment, "
        "then retry."
    ),
    "timeout": (
        "Transcription timed out. Check your connection, then retry."
    ),
    "network": (
        "Transcription failed (network). Check your connection, then "
        "retry."
    ),
    "provider": (
        "Transcription failed on the provider side. Retry; if it "
        "persists, try a different recording."
    ),
    "bad_response": (
        "Transcription returned an unreadable response. Retry; if it "
        "persists, try a different recording."
    ),
    "config": (
        "Transcription is not configured. Set MODEL_API_KEY and "
        "META_ASR_MODEL, then retry."
    ),
}


def user_message_for(category: str) -> str:
    """User-facing guidance for an ASR failure category."""
    return CATEGORY_MESSAGES.get(category, CATEGORY_MESSAGES["provider"])


def _session_id_from(text: str) -> str | None:
    """Pull the provider correlation id from a JSON error body, if any."""
    try:
        payload = json.loads(text)
    except ValueError:
        return None
    if isinstance(payload, dict):
        session = payload.get("sessionId")
        if isinstance(session, str) and session.strip():
            return session.strip()
    return None


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
            ),
            category="no_speech",
        )
    return candidates[0]


def _classify_http_error(status: int, body: str) -> str:
    """Map an HTTP failure to a MetaASRError category."""
    if status in (401, 403):
        return "auth"
    if status == 429:
        return "rate_limit"
    if status == 413:
        return "too_large"
    lowered = body.lower()
    if status == 400 and (
        "unsupported wav" in lowered or "unsupported audio" in lowered
    ):
        return "invalid_audio"
    return "provider"


def transcribe_file(
    path: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    language_bias: str | None = None,
    timeout: float = 120.0,
    diagnostics: dict | None = None,
) -> str:
    """Transcribe a WAV file via Meta Muse Voice Transcribe; return the text.

    The file must already be a conforming mono s16le WAV at 16 or 24
    kHz (see localevoice.audio.normalize); anything else is rejected
    by the provider with an `invalid_audio` error.

    Args:
        path: Filesystem path to a `.wav` file.
        api_key: Override for `MODEL_API_KEY`.
        model: Override for `META_ASR_MODEL`.
        language_bias: Optional recognizer hint (e.g. ``"ar"``). Falls back
            to `LOCALEVOICE_ASR_LANGUAGE_BIAS` when not given. This is a
            hint, not a guarantee of Darija support.
        timeout: HTTP timeout in seconds.
        diagnostics: Optional dict filled with safe provider metadata
            (status_code, session_id, category). Never contains keys,
            audio, or transcripts.

    Raises:
        FileNotFoundError: if the path does not exist or is not a file.
        ValueError: if the path is not a WAV file.
        MetaASRError: categorized failure (see MetaASRError.category).
    """
    info = diagnostics if diagnostics is not None else {}

    def _record(category: str, status: int | None, session: str | None) -> None:
        info["category"] = category
        info["status_code"] = status
        info["session_id"] = session

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    if not path.lower().endswith(".wav"):
        raise ValueError(f"Only WAV files are supported, got: {path}")

    key = api_key if api_key is not None else os.environ.get("MODEL_API_KEY")
    if not key:
        _record("config", None, None)
        raise MetaASRError(
            "Missing API key: set the MODEL_API_KEY environment variable.",
            category="config",
        )
    model_id = model if model is not None else os.environ.get("META_ASR_MODEL")
    if not model_id:
        _record("config", None, None)
        raise MetaASRError(
            "Missing model identifier: set META_ASR_MODEL.", category="config"
        )
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
    except requests.Timeout as exc:
        _record("timeout", None, None)
        raise MetaASRError(
            _redact(f"ASR request timed out: {exc}", [key]),
            category="timeout",
        ) from exc
    except requests.RequestException as exc:
        _record("network", None, None)
        raise MetaASRError(
            _redact(f"ASR request failed: {exc}", [key]), category="network"
        ) from exc

    if response.status_code >= 400:
        detail = _redact(response.text[:1000], [key])
        session = _session_id_from(response.text)
        category = _classify_http_error(response.status_code, response.text)
        _record(category, response.status_code, session)
        raise MetaASRError(
            f"ASR request failed with status {response.status_code}: {detail}",
            category=category,
            status_code=response.status_code,
            session_id=session,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        detail = _redact(response.text[:1000], [key])
        _record("bad_response", response.status_code, None)
        raise MetaASRError(
            f"ASR response was not valid JSON (status "
            f"{response.status_code}): {detail}",
            category="bad_response",
            status_code=response.status_code,
        ) from exc

    try:
        transcript = _extract_transcript(payload, key)
    except MetaASRError as exc:
        session = (
            payload.get("sessionId") if isinstance(payload, dict) else None
        )
        _record(
            "no_speech",
            response.status_code,
            session if isinstance(session, str) else None,
        )
        exc.status_code = response.status_code
        exc.session_id = _session_id_from(json.dumps(payload))
        raise
    _record("ok", response.status_code, _session_id_from(response.text))
    return transcript
