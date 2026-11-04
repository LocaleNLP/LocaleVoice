"""Unit tests for UI orchestration (flow.py). No Streamlit, no network.

The backend is injected as mocks, so these tests prove orchestration:
validation, transcript handoff, and honest error propagation. They do not
validate the real providers.
"""

from __future__ import annotations

import os
from unittest.mock import Mock

import pytest

from audio_fixtures import make_wav_bytes

from localevoice.knowledge.corpus import Corpus, Document
from localevoice.pipeline.answer import AnswerResult, LanguageInfo
from localevoice.providers.meta_asr import MetaASRError
from localevoice.providers.meta_chat import MetaChatError
from localevoice.ui.flow import (
    ValidatedUpload,
    answer_confirmed_text,
    safe_html_paragraph,
    transcribe_upload,
    validate_audio_upload,
)

WAV_BYTES = make_wav_bytes()
FAKE_WAV_BYTES = (
    b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fake-audio-payload" + b"\x00" * 32
)


def _corpus():
    return Corpus(documents=[], manifest={}, corpus_dir=".")


def test_valid_wav_upload_passes():
    upload = validate_audio_upload("question.wav", WAV_BYTES)
    assert isinstance(upload, ValidatedUpload)
    assert upload.filename == "question.wav"
    assert upload.data == WAV_BYTES


def test_valid_wav_upload_case_insensitive_extension():
    assert validate_audio_upload("Q.WAV", WAV_BYTES).filename == "Q.WAV"


@pytest.mark.parametrize(
    "filename,data",
    [
        (None, WAV_BYTES),
        ("", WAV_BYTES),
        ("question.wav", None),
        ("question.wav", b""),
    ],
)
def test_empty_audio_rejected(filename, data):
    with pytest.raises(ValueError, match="No audio"):
        validate_audio_upload(filename, data)


def test_unsupported_extension_rejected():
    with pytest.raises(ValueError, match="Unsupported audio format"):
        validate_audio_upload("question.ogg", WAV_BYTES)
    with pytest.raises(ValueError, match="Unsupported audio format"):
        validate_audio_upload("question.exe", WAV_BYTES)


def test_compressed_extensions_accepted_at_precheck():
    mp3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 100
    assert validate_audio_upload("question.mp3", mp3).filename == "question.mp3"
    m4a = b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 100
    assert validate_audio_upload("q.M4A", m4a).filename == "q.M4A"
    webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 100
    assert validate_audio_upload("q.webm", webm).filename == "q.webm"


def test_non_wav_bytes_rejected():
    with pytest.raises(ValueError, match="not a supported audio"):
        validate_audio_upload("question.wav", b"x" * 100)


def test_oversize_audio_rejected():
    with pytest.raises(ValueError, match="too large"):
        validate_audio_upload("question.wav", WAV_BYTES, max_bytes=10)


def test_transcribe_upload_calls_provider_with_wav_path():
    transcribe_fn = Mock(return_value="القمح مزيان؟")
    upload = ValidatedUpload(filename="q.wav", data=WAV_BYTES)
    assert transcribe_upload(upload, transcribe_fn=transcribe_fn) == "القمح مزيان؟"
    (path,), _ = transcribe_fn.call_args
    assert path.endswith(".wav")


def test_transcribe_upload_propagates_asr_failure():
    transcribe_fn = Mock(side_effect=MetaASRError("status 401: Unauthorized"))
    upload = ValidatedUpload(filename="q.wav", data=WAV_BYTES)
    with pytest.raises(MetaASRError, match="401"):
        transcribe_upload(upload, transcribe_fn=transcribe_fn)


def _result(**overrides):
    base = {
        "question": "q",
        "answer_text": "a",
        "language": LanguageInfo(
            requested=None, inferred="unknown", uncertain=True
        ),
        "source_ids_supplied": [],
        "evidence": [],
        "insufficient_evidence": False,
        "model": "m",
        "elapsed_ms": 1,
        "error": None,
    }
    base.update(overrides)
    return AnswerResult(**base)


def test_confirmed_text_passed_to_pipeline_verbatim():
    answer_fn = Mock(return_value=_result())
    answer_confirmed_text("  edited transcript هنا  ", _corpus(), answer_fn=answer_fn)
    (question, _corpus_arg), _ = answer_fn.call_args
    assert question == "  edited transcript هنا  "


def test_empty_confirmed_text_rejected_before_pipeline():
    answer_fn = Mock(return_value=_result())
    with pytest.raises(ValueError, match="empty"):
        answer_confirmed_text("   ", _corpus(), answer_fn=answer_fn)
    answer_fn.assert_not_called()


def test_evidence_result_returned_untouched():
    evidence = [
        {
            "document_id": "feedipedia-wheat-grain",
            "title": "Wheat grain",
            "publisher": "P",
            "source_url": "https://example.org",
            "score": 2,
            "matched_terms": ["wheat"],
        }
    ]
    answer_fn = Mock(
        return_value=_result(
            answer_text="Grounded. [feedipedia-wheat-grain]",
            source_ids_supplied=["feedipedia-wheat-grain"],
            evidence=evidence,
        )
    )
    result = answer_confirmed_text("wheat?", _corpus(), answer_fn=answer_fn)
    assert result.insufficient_evidence is False
    assert result.evidence == evidence
    assert "[feedipedia-wheat-grain]" in result.answer_text


def test_insufficient_result_returned_untouched():
    answer_fn = Mock(
        return_value=_result(
            answer_text="I could not find relevant evidence.",
            insufficient_evidence=True,
            model=None,
            elapsed_ms=None,
        )
    )
    result = answer_confirmed_text("capital?", _corpus(), answer_fn=answer_fn)
    assert result.insufficient_evidence is True
    assert result.evidence == []


def test_pipeline_error_propagates_with_detail():
    answer_fn = Mock(
        return_value=_result(
            answer_text="failed",
            model="m",
            elapsed_ms=5,
            error={"type": "MetaChatError", "message": "boom 503"},
        )
    )
    result = answer_confirmed_text("wheat?", _corpus(), answer_fn=answer_fn)
    assert result.error["type"] == "MetaChatError"
    assert "503" in result.error["message"]


def test_pipeline_exception_propagates():
    answer_fn = Mock(side_effect=MetaChatError("boom"))
    with pytest.raises(MetaChatError, match="boom"):
        answer_confirmed_text("wheat?", _corpus(), answer_fn=answer_fn)


def test_safe_html_paragraph_escapes_untrusted_text():
    out = safe_html_paragraph('<script>alert("x")</script> مرحبا', "lv-answer")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "مرحبا" in out
    assert 'dir="auto"' in out


def test_safe_html_paragraph_escapes_css_class():
    out = safe_html_paragraph("hi", 'x" onmouseover="alert(1)')
    assert '" onmouseover="' not in out  # no attribute breakout
    assert "&quot;" in out
    assert out.startswith("<p class=\"")


def test_transcribe_upload_cleans_temp_file_on_success(tmp_path):
    seen = {}

    def _ok(path, **kwargs):
        seen["path"] = path
        assert os.path.isfile(path)
        return "transcript"

    upload = ValidatedUpload(filename="q.wav", data=WAV_BYTES)
    assert transcribe_upload(upload, transcribe_fn=_ok) == "transcript"
    assert not os.path.exists(seen["path"])


def test_transcribe_upload_cleans_temp_file_on_failure():
    seen = {}

    def _fail(path, **kwargs):
        seen["path"] = path
        raise MetaASRError("boom")

    upload = ValidatedUpload(filename="q.wav", data=WAV_BYTES)
    with pytest.raises(MetaASRError, match="boom"):
        transcribe_upload(upload, transcribe_fn=_fail)
    assert not os.path.exists(seen["path"])
