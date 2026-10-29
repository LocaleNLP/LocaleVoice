"""Meta Model API chat provider (Milestone 1 smoke-test primitive).

Uses the OpenAI Python SDK pointed at the Meta base URL. No local inference.
"""

from __future__ import annotations

import os

META_BASE_URL = "https://api.meta.ai/v1"

# Short test prompt: asks the configured model for one identifiable phrase so
# a smoke run can confirm the response really came from the hosted model.
SMOKE_PROMPT = (
    "Reply with exactly this phrase and nothing else: LOCALEVOICE_SMOKE_OK"
)
SMOKE_EXPECTED_PHRASE = "LOCALEVOICE_SMOKE_OK"


class ConfigurationError(Exception):
    """Raised when required environment configuration is missing."""


class MetaChatError(Exception):
    """Raised when a Meta Model API chat request fails or yields no text."""


def _redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        if secret and secret in text:
            text = text.replace(secret, "***REDACTED***")
    return text


def resolve_model(model: str | None = None) -> str:
    """Resolve the configured chat model identifier or raise."""
    model_id = model if model is not None else os.environ.get("META_CHAT_MODEL")
    if not model_id:
        raise ConfigurationError(
            "Missing model identifier: set META_CHAT_MODEL."
        )
    return model_id


def chat_complete(
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str = META_BASE_URL,
    timeout: float = 60.0,
) -> str:
    """Send a chat request to the Meta Model API; return its text.

    Single source for Meta chat access. Raises ConfigurationError if the
    API key or model identifier is missing; MetaChatError if the request
    fails or the response contains no text.
    """
    key = api_key if api_key is not None else os.environ.get("MODEL_API_KEY")
    if not key:
        raise ConfigurationError(
            "Missing API key: set the MODEL_API_KEY environment variable."
        )
    model_id = resolve_model(model)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, base_url=base_url)
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            timeout=timeout,
        )
    except Exception as exc:  # SDK/request failure: keep diagnostics, drop secrets
        raise MetaChatError(
            _redact(f"Meta chat request failed: {exc}", [key])
        ) from exc

    text = ""
    try:
        choices = getattr(response, "choices", None) or []
        if choices:
            message = getattr(choices[0], "message", None)
            content = getattr(message, "content", None) if message else None
            if isinstance(content, str):
                text = content.strip()
    except Exception as exc:
        raise MetaChatError(
            _redact(f"Could not parse Meta chat response: {exc}", [key])
        ) from exc

    if not text:
        raise MetaChatError(
            "Meta chat response contained no text; treating as failure."
        )
    return text


def verify_chat(
    prompt: str = SMOKE_PROMPT,
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str = META_BASE_URL,
    timeout: float = 60.0,
) -> str:
    """Send one short chat request to the Meta Model API; return its text.

    Raises:
        ConfigurationError: if the API key or model identifier is missing.
        MetaChatError: if the request fails or the response contains no text.
    """
    return chat_complete(
        [{"role": "user", "content": prompt}],
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=timeout,
    )
