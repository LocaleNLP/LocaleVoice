"""Unit tests for the answer pipeline. Chat calls are mocked; no network."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from localevoice.knowledge.corpus import Corpus, CorpusError, Document
from localevoice.pipeline.answer import (
    AnswerResult,
    answer_question,
    build_messages,
    find_citations,
    infer_language,
)
from localevoice.providers.meta_chat import ConfigurationError, MetaChatError


def _doc(doc_id="doc-1", content="Wheat is an energy source for ruminants."):
    return Document(
        document_id=doc_id,
        title="Wheat grain",
        publisher="P",
        source_url="https://example.org",
        retrieved_at="2026-10-29",
        language="en",
        crop_or_topic="wheat",
        content=content,
        usage_or_license_notes="test",
    )


def _corpus(*docs):
    return Corpus(
        documents=list(docs), manifest={"corpus_version": "t"}, corpus_dir="."
    )


def test_build_messages_includes_evidence_and_rules():
    from localevoice.knowledge.retrieve import retrieve

    (evidence,) = retrieve("wheat ruminants", [_doc()])
    messages = build_messages("Is wheat good?", [evidence], infer_language("x"))
    assert messages[0]["role"] == "system"
    assert "ONLY" in messages[0]["content"]
    user = messages[1]["content"]
    assert "Is wheat good?" in user
    assert "[doc-1]" in user
    assert "energy source" in user


def test_success_path_returns_structured_result(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    chat_fn = Mock(return_value="Wheat helps. [doc-1]")
    result = answer_question("Is wheat good?", _corpus(_doc()), chat_fn=chat_fn)
    assert isinstance(result, AnswerResult)
    assert result.answer_text == "Wheat helps. [doc-1]"
    assert result.source_ids_supplied == ["doc-1"]
    assert result.insufficient_evidence is False
    assert result.model == "test-model"
    assert result.elapsed_ms is not None and result.elapsed_ms >= 0
    assert result.error is None
    assert result.evidence[0]["document_id"] == "doc-1"
    assert result.evidence[0]["score"] >= 1
    chat_fn.assert_called_once()


def test_no_evidence_returns_insufficient_without_model_call():
    chat_fn = Mock(return_value="should never be called")
    result = answer_question(
        "شنو هي عاصمة المغرب؟", _corpus(_doc()), chat_fn=chat_fn
    )
    assert result.insufficient_evidence is True
    assert result.source_ids_supplied == []
    assert result.evidence == []
    assert result.model is None
    assert "could not find relevant evidence" in result.answer_text
    chat_fn.assert_not_called()


def test_min_score_gates_weak_matches():
    chat_fn = Mock(return_value="never")
    result = answer_question(
        "wheat", _corpus(_doc()), min_score=5, chat_fn=chat_fn
    )
    assert result.insufficient_evidence is True
    chat_fn.assert_not_called()


def test_chat_failure_returns_error_without_fabrication(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    chat_fn = Mock(side_effect=MetaChatError("boom 503"))
    result = answer_question("wheat?", _corpus(_doc()), chat_fn=chat_fn)
    assert result.error is not None
    assert result.error["type"] == "MetaChatError"
    assert "503" in result.error["message"]
    assert "failed" in result.answer_text
    assert result.source_ids_supplied == ["doc-1"]  # supplied, not cited


def test_missing_model_config_returns_error(monkeypatch):
    monkeypatch.delenv("META_CHAT_MODEL", raising=False)
    chat_fn = Mock(return_value="never")
    result = answer_question("wheat?", _corpus(_doc()), chat_fn=chat_fn)
    assert result.error is not None
    assert result.error["type"] == "ConfigurationError"
    chat_fn.assert_not_called()


def test_empty_question_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        answer_question("   ", _corpus(_doc()))


def test_empty_corpus_rejected():
    with pytest.raises(CorpusError, match="empty"):
        answer_question("wheat?", _corpus())


def test_find_citations_extracts_ids():
    assert find_citations("See [doc-1] and [feedipedia-wheat-grain].") == [
        "doc-1",
        "feedipedia-wheat-grain",
    ]
    assert find_citations("no citations here") == []


def test_infer_language_marks_uncertainty():
    arabic = infer_language("القمح مزيان؟")
    assert arabic.uncertain is True
    assert "uncertain" in arabic.inferred
    latin = infer_language("Is wheat good?")
    assert latin.uncertain is True
    explicit = infer_language("القمح؟", requested="darija")
    assert explicit.uncertain is False
    assert explicit.inferred == "darija"


def test_run_record_serialization_has_no_secrets(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    monkeypatch.setenv("MODEL_API_KEY", "super-secret-key")
    chat_fn = Mock(return_value="Answer. [doc-1]")
    result = answer_question("wheat?", _corpus(_doc()), chat_fn=chat_fn)
    record = result.to_run_record()
    blob = str(record)
    assert "super-secret-key" not in blob
    assert "MODEL_API_KEY" not in blob
    assert record["answer_text"] == "Answer. [doc-1]"
    assert record["language"]["uncertain"] is True
