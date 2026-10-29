"""Mocked unit tests for the Meta chat provider. No network access."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from localevoice.providers.meta_chat import (
    META_BASE_URL,
    SMOKE_PROMPT,
    ConfigurationError,
    MetaChatError,
    verify_chat,
)


def _fake_response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def test_verify_chat_success_returns_text_and_uses_meta_endpoint():
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = (
            _fake_response("LOCALEVOICE_SMOKE_OK")
        )
        text = verify_chat(api_key="test-key", model="test-model")

    assert text == "LOCALEVOICE_SMOKE_OK"
    _, kwargs = mock_client_cls.call_args
    assert kwargs["api_key"] == "test-key"
    assert kwargs["base_url"] == META_BASE_URL
    assert META_BASE_URL == "https://api.meta.ai/v1"
    _, create_kwargs = (
        mock_client_cls.return_value.chat.completions.create.call_args
    )
    assert create_kwargs["model"] == "test-model"
    assert create_kwargs["messages"] == [
        {"role": "user", "content": SMOKE_PROMPT}
    ]


def test_verify_chat_missing_key_fails(monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="MODEL_API_KEY"):
        verify_chat(model="test-model")


def test_verify_chat_missing_model_fails(monkeypatch):
    monkeypatch.delenv("META_CHAT_MODEL", raising=False)
    with pytest.raises(ConfigurationError, match="META_CHAT_MODEL"):
        verify_chat(api_key="test-key")


def test_verify_chat_request_failure_preserves_diagnostics_without_key():
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.side_effect = (
            Exception("503 Service Unavailable")
        )
        with pytest.raises(MetaChatError) as exc_info:
            verify_chat(api_key="super-secret-key", model="test-model")

    assert "503" in str(exc_info.value)
    assert "super-secret-key" not in str(exc_info.value)


@pytest.mark.parametrize("content", ["", "   ", None])
def test_verify_chat_empty_response_fails(content):
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = (
            _fake_response(content)
        )
        with pytest.raises(MetaChatError, match="no text"):
            verify_chat(api_key="test-key", model="test-model")


def test_verify_chat_no_choices_fails():
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = (
            SimpleNamespace(choices=[])
        )
        with pytest.raises(MetaChatError, match="no text"):
            verify_chat(api_key="test-key", model="test-model")
