"""Unit tests for evidence traces and citation validation. No network."""

from __future__ import annotations

from unittest.mock import Mock

from localevoice.knowledge.corpus import load_corpus
from localevoice.pipeline.answer import answer_question
from localevoice.pipeline.trace import build_trace, validate_citations


def test_validate_citations_contained_and_invalid():
    ok = validate_citations("A. [doc-1] B. [doc-2]", ["doc-1", "doc-2"])
    assert ok == {
        "found": ["doc-1", "doc-2"],
        "supplied": ["doc-1", "doc-2"],
        "contained": True,
        "invalid": [],
        "malformed": [],
        "syntax_ok": True,
    }
    bad = validate_citations("A. [doc-1] B. [invented]", ["doc-1"])
    assert bad["contained"] is False
    assert bad["invalid"] == ["invented"]
    assert bad["found"] == ["doc-1", "invented"]


def test_validate_citations_empty_answer():
    check = validate_citations("no citations here", ["doc-1"])
    assert check["found"] == []
    assert check["contained"] is True


def test_trace_on_answered_path(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    monkeypatch.setenv("MODEL_API_KEY", "super-secret-key")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="Answer. [feedipedia-wheat-grain]")
    result = answer_question("القمح واش مزيان للبقر؟", corpus, chat_fn=chat_fn)
    trace = result.trace
    assert trace["status"] == "answered"
    assert trace["detected_intent"] == "agricultural_question"
    assert trace["detected_category"] == "Cereals"
    assert "قمح" in trace["extracted_keywords"]
    assert trace["selected_evidence_ids"] == ["feedipedia-wheat-grain"]
    assert trace["sufficient_evidence"] is True
    assert trace["clarification_requested"] is False
    assert trace["model_called"] is True
    assert trace["model_id"] == "test-model"
    assert trace["citation_check"]["contained"] is True
    assert trace["thresholds"] == {"min_score": 1, "top_k": 3}
    wheat = trace["documents_considered"]["feedipedia-wheat-grain"]
    assert wheat["selected"] is True and wheat["reason"] == "selected"
    cowpea = trace["documents_considered"]["feedipedia-cowpea-seeds"]
    assert cowpea["selected"] is False
    assert "super-secret-key" not in str(trace)
    assert "MODEL_API_KEY" not in str(trace)


def test_trace_on_insufficient_path():
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    trace = result.trace
    assert trace["status"] == "insufficient"
    assert trace["sufficient_evidence"] is False
    assert trace["clarification_requested"] is True
    assert trace["model_called"] is False
    assert trace["citation_check"] is None
    assert trace["selected_evidence_ids"] == []
    for doc_id, info in trace["documents_considered"].items():
        assert info["selected"] is False
        assert info["reason"]  # every rejection explained


def test_trace_on_intent_path():
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question("السلام عليكم", corpus, chat_fn=chat_fn)
    assert result.trace["status"] == "intent:greeting"
    assert result.trace["model_called"] is False
    chat_fn.assert_not_called()


def test_trace_records_rejection_reasons():
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question(
        "protein", corpus, chat_fn=chat_fn, top_k=1, min_score=1
    )
    considered = result.trace["documents_considered"]
    reasons = {d: info["reason"] for d, info in considered.items()}
    # Alfalfa matches "protein" but is pending-review: excluded from
    # evidence, still visible in diagnostics (Milestone 5.1). Since 6B
    # it no longer consumes a rank slot, so olive-cake fills top_k=1.
    assert "excluded: review_status=pending-review" in reasons[
        "feedipedia-alfalfa"
    ]
    assert reasons["feedipedia-olive-cake"] == "selected"
    assert "beyond top_k" in reasons["feedipedia-wheat-grain"]
    assert reasons["feedipedia-cowpea-seeds"] == "no matched terms"


def test_trace_below_min_score_reason():
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question("wheat", corpus, chat_fn=chat_fn, min_score=5)
    considered = result.trace["documents_considered"]
    assert "below min_score" in considered["feedipedia-wheat-grain"]["reason"]
    assert result.trace["sufficient_evidence"] is False


def test_build_trace_shape():
    trace = build_trace(
        question="q",
        normalized_question="q",
        intent="unclear",
        category=None,
        keywords=["q"],
        considered={},
        selected_ids=[],
        min_score=1,
        top_k=3,
        sufficient=False,
        clarification_requested=False,
        model_called=False,
        model_id=None,
        citation_check=None,
        status="insufficient",
    )
    assert trace["question"] == "q"
    assert trace["error_type"] is None
