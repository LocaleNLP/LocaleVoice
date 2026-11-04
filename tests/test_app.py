"""Headless UI tests via Streamlit AppTest (mocked providers, no network).

These exercise the real app.py widget flow (upload -> review -> answer,
typed fallback, failures) with the HTTP/SDK boundary mocked. They are
NOT browser verification and NOT provider validation.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")
WAV = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"\x00" * 100


def _asr_response(transcript):
    return SimpleNamespace(
        status_code=200,
        text=f'{{"transcript": "{transcript}"}}',
        json=lambda: {"transcript": transcript},
    )


def _chat_response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def _run():
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.run()
    assert not list(app.exception)
    return app


def _click(app, label_part):
    matches = [b for b in app.button if label_part in b.label]
    assert matches, f"button {label_part!r} not found"
    matches[0].click()
    app.run()
    assert not list(app.exception)


def test_startup_initial_state():
    app = _run()
    assert [t.value for t in app.title] == ["LocaleVoice 🌾"]
    assert len(app.file_uploader) == 1
    assert len(app.audio_input) == 1


def test_upload_transcribe_confirm_answer_flow(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    with (
        patch("localevoice.providers.meta_asr.requests.post") as post,
        patch("openai.OpenAI") as cls,
    ):
        post.return_value = _asr_response("wheat for cattle")
        cls.return_value.chat.completions.create.return_value = _chat_response(
            "Grounded. [feedipedia-wheat-grain]"
        )
        app = _run()
        app.file_uploader[0].set_value(("q.wav", WAV, "audio/wav"))
        with patch("streamlit.audio") as audio:
            app.run()
        assert audio.call_count == 1  # upload plays back before transcribing
        (played,), _ = audio.call_args
        assert played == WAV
        _click(app, "Transcribe upload")
        assert [h.value for h in app.header] == ["Review"]
        assert post.call_count == 1
        # edit before confirming: the edited text must reach the pipeline
        app.text_area[0].set_value("edited wheat question")
        app.run()
        _click(app, "Confirm")
        assert [h.value for h in app.header] == ["Answer"]
        assert cls.return_value.chat.completions.create.call_count == 1
        _, kwargs = cls.return_value.chat.completions.create.call_args
        assert "edited wheat question" in kwargs["messages"][1]["content"]


def test_invalid_upload_content_shows_failure_without_provider_call():
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as post:
        app = _run()
        app.file_uploader[0].set_value(("q.wav", b"x" * 100, "audio/wav"))
        app.run()
        _click(app, "Transcribe upload")
        assert [h.value for h in app.header] == []  # stayed on ask stage
        assert len(app.error) == 1
        assert "WAV" in app.error[0].value
        post.assert_not_called()


def test_wrong_extension_never_reaches_provider():
    # The widget itself only accepts .wav; either way no provider call happens.
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as post:
        app = _run()
        try:
            app.file_uploader[0].set_value(("q.mp3", WAV, "audio/mpeg"))
            app.run()
        except Exception:
            pass
        post.assert_not_called()


def test_oversize_upload_rejected():
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as post:
        app = _run()
        big = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * (11 * 1024 * 1024)
        app.file_uploader[0].set_value(("big.wav", big, "audio/wav"))
        app.run()
        _click(app, "Transcribe upload")
        assert len(app.error) == 1
        assert "too large" in app.error[0].value
        post.assert_not_called()


def test_asr_failure_renders_failure_state():
    with patch("localevoice.providers.meta_asr.requests.post") as post:
        post.return_value = SimpleNamespace(status_code=401, text="Unauthorized")
        app = _run()
        app.file_uploader[0].set_value(("q.wav", WAV, "audio/wav"))
        app.run()
        _click(app, "Transcribe upload")
        assert len(app.error) == 1
        assert "Transcription failed" in app.error[0].value


def test_typed_fallback_insufficient_evidence_path(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    with patch("openai.OpenAI") as cls:
        app = _run()
        app.text_area[0].set_value("كلام غير مفهوم xyzzy")
        app.run()
        _click(app, "Continue with typed text")
        assert [h.value for h in app.header] == ["Review"]
        _click(app, "Confirm")
        assert [h.value for h in app.header] == ["Answer"]
        assert len(app.warning) == 1
        assert "Not enough evidence" in app.warning[0].value
        cls.return_value.chat.completions.create.assert_not_called()


def test_unsupported_domain_shows_info_banner(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    with patch("openai.OpenAI") as cls:
        app = _run()
        app.text_area[0].set_value("What is the capital of Morocco?")
        app.run()
        _click(app, "Continue with typed text")
        _click(app, "Confirm")
        assert [h.value for h in app.header] == ["Answer"]
        assert len(app.warning) == 0
        assert any("agricultural scope" in i.value for i in app.info)
        cls.return_value.chat.completions.create.assert_not_called()


def test_chat_failure_renders_failure_state(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    with patch("openai.OpenAI") as cls:
        cls.return_value.chat.completions.create.side_effect = Exception("boom 503")
        app = _run()
        app.text_area[0].set_value("Is wheat good for cattle?")
        app.run()
        _click(app, "Continue with typed text")
        _click(app, "Confirm")
        assert len(app.error) == 1
        assert "Answer generation failed" in app.error[0].value


def test_clarify_flow_answers_after_context(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    with patch("openai.OpenAI") as cls:
        cls.return_value.chat.completions.create.return_value = _chat_response(
            "Answer. [feedipedia-wheat-grain]"
        )
        app = _run()
        app.text_area[0].set_value("شحال كتسقي الزرع فالسيمانة؟")
        app.run()
        _click(app, "Continue with typed text")
        assert [h.value for h in app.header] == ["Review"]
        _click(app, "Confirm")
        assert [h.value for h in app.header] == ["One question"]
        assert cls.return_value.chat.completions.create.call_count == 0
        # Form widgets commit on submit: set + click in the same cycle.
        app.text_area[0].set_value("القمح")
        [b for b in app.button if b.label == "Send"][0].click()
        app.run()
        assert not list(app.exception)
        assert [h.value for h in app.header] == ["Answer"]
        assert cls.return_value.chat.completions.create.call_count == 1


def test_clarify_flow_finish_abstains_without_evidence(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    with patch("openai.OpenAI") as cls:
        app = _run()
        app.text_area[0].set_value("شحال كتسقي الزرع فالسيمانة؟")
        app.run()
        _click(app, "Continue with typed text")
        _click(app, "Confirm")
        assert [h.value for h in app.header] == ["One question"]
        app.text_area[0].set_value("الخضرة")
        [b for b in app.button if b.label == "Send"][0].click()
        app.run()
        assert not list(app.exception)
        assert [h.value for h in app.header] == ["One question"]
        assert len(app.error) == 0  # genuine retry, not an empty reply
        _click(app, "Finish without answer")
        assert [h.value for h in app.header] == ["Answer"]
        assert len(app.warning) == 1
        cls.return_value.chat.completions.create.assert_not_called()


def test_retry_clears_failure():
    app = _run()
    app.text_area[0].set_value("   ")
    app.run()
    _click(app, "Continue with typed text")
    assert len(app.error) == 1
    _click(app, "Retry")
    assert len(app.error) == 0


def test_start_over_returns_to_ask_stage(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    with patch("openai.OpenAI"):
        app = _run()
        app.text_area[0].set_value("What is the capital of Morocco?")
        app.run()
        _click(app, "Continue with typed text")
        _click(app, "Confirm")
        assert [h.value for h in app.header] == ["Answer"]
        _click(app, "Ask another question")
        assert [h.value for h in app.header] == []
        assert len(app.file_uploader) == 1
