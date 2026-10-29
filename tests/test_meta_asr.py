"""Mocked unit tests for the Meta ASR provider. No network access."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from localevoice.providers.meta_asr import (
    ASR_ENCODING,
    ASR_MODE,
    ASR_URL,
    MetaASRError,
    transcribe_file,
)


def _wav(tmp_path, name="sample.wav"):
    path = tmp_path / name
    path.write_bytes(b"RIFF....WAVEfake-audio-bytes")
    return str(path)


def _ok_response(payload):
    return SimpleNamespace(status_code=200, text=json.dumps(payload), json=lambda: payload)


def test_transcribe_success_sends_documented_multipart_shape(tmp_path):
    wav = _wav(tmp_path)
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as mock_post:
        mock_post.return_value = _ok_response({"text": "hello world"})
        transcript = transcribe_file(
            wav, api_key="test-key", model="test-asr-model"
        )

    assert transcript == "hello world"
    assert ASR_URL == "https://api.meta.ai/v1/asr/transcribe"
    assert ASR_MODE == "PUSH_TO_TALK"
    assert ASR_ENCODING == "WAV"
    (url,), kwargs = mock_post.call_args
    assert url == ASR_URL
    assert kwargs["headers"] == {"Authorization": "Bearer test-key"}
    request_part = json.loads(kwargs["data"]["request"])
    assert request_part["model"] == "test-asr-model"
    assert request_part["mode"] == "PUSH_TO_TALK"
    assert request_part["audioEncoding"] == "WAV"
    assert "language" not in request_part
    filename, _, content_type = kwargs["files"]["audio"]
    assert filename == "sample.wav"
    assert content_type == "audio/wav"


def test_transcribe_language_bias_is_sent_as_hint(tmp_path):
    wav = _wav(tmp_path)
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as mock_post:
        mock_post.return_value = _ok_response({"text": "ok"})
        transcribe_file(
            wav, api_key="k", model="m", language_bias="ar"
        )

    request_part = json.loads(mock_post.call_args[1]["data"]["request"])
    assert request_part["language"] == "ar"


def test_transcribe_missing_file_fails_before_network(tmp_path):
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as mock_post:
        with pytest.raises(FileNotFoundError):
            transcribe_file(
                str(tmp_path / "nope.wav"), api_key="k", model="m"
            )
    mock_post.assert_not_called()


def test_transcribe_non_wav_rejected_before_network(tmp_path):
    mp3 = tmp_path / "sample.mp3"
    mp3.write_bytes(b"fake")
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as mock_post:
        with pytest.raises(ValueError, match="WAV"):
            transcribe_file(str(mp3), api_key="k", model="m")
    mock_post.assert_not_called()


def test_transcribe_missing_key_fails(tmp_path, monkeypatch):
    wav = _wav(tmp_path)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(MetaASRError, match="MODEL_API_KEY"):
        transcribe_file(wav, model="m")


def test_transcribe_http_error_preserves_status_without_key(tmp_path):
    wav = _wav(tmp_path)
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as mock_post:
        mock_post.return_value = SimpleNamespace(
            status_code=401, text="unauthorized"
        )
        with pytest.raises(MetaASRError) as exc_info:
            transcribe_file(wav, api_key="super-secret-key", model="m")

    assert "401" in str(exc_info.value)
    assert "unauthorized" in str(exc_info.value)
    assert "super-secret-key" not in str(exc_info.value)


def test_transcribe_invalid_json_fails(tmp_path):
    wav = _wav(tmp_path)
    bad = SimpleNamespace(status_code=200, text="<html>oops</html>")

    def _raise():
        raise ValueError("bad json")

    bad.json = _raise
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as mock_post:
        mock_post.return_value = bad
        with pytest.raises(MetaASRError, match="not valid JSON"):
            transcribe_file(wav, api_key="k", model="m")


@pytest.mark.parametrize(
    "payload", [{"text": "   "}, {"text": ""}, {}, {"results": []}]
)
def test_transcribe_empty_transcript_fails(tmp_path, payload):
    wav = _wav(tmp_path)
    with patch(
        "localevoice.providers.meta_asr.requests.post"
    ) as mock_post:
        mock_post.return_value = _ok_response(payload)
        with pytest.raises(MetaASRError, match="no usable transcript"):
            transcribe_file(wav, api_key="k", model="m")


def test_transcribe_accepts_nested_result_shape(tmp_path):
    wav = _wav(tmp_path)
    with patch("localevoice.providers.meta_asr.requests.post") as mock_post:
        mock_post.return_value = _ok_response(
            {"results": [{"transcript": "nested ok"}]}
        )
        assert (
            transcribe_file(wav, api_key="k", model="m") == "nested ok"
        )


def test_transcribe_accepts_live_turns_shape(tmp_path):
    # Shape observed from the live endpoint: top-level transcript plus turns.
    wav = _wav(tmp_path)
    with patch("localevoice.providers.meta_asr.requests.post") as mock_post:
        mock_post.return_value = _ok_response(
            {
                "sessionId": "voyager/transcribe/abc",
                "transcript": "",
                "audioDurationMs": 1040,
                "turns": [{"transcript": "turns ok"}],
            }
        )
        assert (
            transcribe_file(wav, api_key="k", model="m") == "turns ok"
        )
