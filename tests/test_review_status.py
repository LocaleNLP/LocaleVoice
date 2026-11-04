"""Milestone 5.1: review-status enforcement.

Only verified excerpts may back farmer-facing answers. pending-review,
rejected, archived (and unknown statuses) are excluded from evidence
selection but remain visible in diagnostics with an explicit reason.
Chat calls mocked throughout.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from localevoice.knowledge.corpus import Corpus, Document, is_answer_eligible
from localevoice.pipeline.answer import answer_question, find_citations


def _doc(doc_id, text, status="verified-excerpt", keywords=()):
    return Document(
        id=doc_id,
        title=f"Title {doc_id}",
        source_name="P",
        source_url="https://example.org",
        category="Cereals",
        crop_or_species="wheat",
        excerpt=text,
        language="en",
        date_accessed="2026-10-29",
        review_status=status,
        keywords=tuple(keywords),
    )


def _corpus(*docs):
    return Corpus(documents=list(docs), manifest={}, corpus_dir="test")


def test_eligibility_matrix():
    assert is_answer_eligible(_doc("a", "wheat", "verified-excerpt")) is True
    for status in ("pending-review", "rejected", "archived", "bogus", ""):
        assert is_answer_eligible(_doc("a", "wheat", status)) is False


@pytest.mark.parametrize(
    "status", ["pending-review", "rejected", "archived"]
)
def test_non_verified_match_abstains(status):
    corpus = _corpus(_doc("only", "wheat cattle feed", status))
    chat_fn = Mock(return_value="must not be called")
    result = answer_question("wheat for cattle?", corpus, chat_fn=chat_fn)
    assert result.insufficient_evidence is True
    assert result.evidence == []
    assert result.source_ids_supplied == []
    chat_fn.assert_not_called()
    considered = result.trace["documents_considered"]["only"]
    assert considered["selected"] is False
    assert considered["reason"].startswith("excluded: review_status=" + status)


def test_verified_doc_remains_retrievable(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = _corpus(_doc("good", "wheat cattle feed"))
    chat_fn = Mock(return_value="Answer. [good]")
    result = answer_question("wheat for cattle?", corpus, chat_fn=chat_fn)
    assert result.insufficient_evidence is False
    assert result.source_ids_supplied == ["good"]
    assert result.trace["documents_considered"]["good"]["reason"] == "selected"


def test_mixed_corpus_uses_only_verified(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = _corpus(
        _doc("good", "wheat cattle feed"),
        _doc("pend", "wheat cattle feed", "pending-review"),
    )
    chat_fn = Mock(return_value="Answer. [good]")
    result = answer_question("wheat for cattle?", corpus, chat_fn=chat_fn)
    assert result.source_ids_supplied == ["good"]
    assert "pend" not in result.trace["selected_evidence_ids"]
    for citation in find_citations(result.answer_text):
        assert citation in result.source_ids_supplied


def test_pending_only_match_abstains_with_exclusion_reason():
    corpus = _corpus(
        _doc("pend", "luzerne fourrage vaches", "pending-review")
    )
    chat_fn = Mock(return_value="must not be called")
    result = answer_question(
        "La luzerne est-elle un bon fourrage ?", corpus, chat_fn=chat_fn
    )
    assert result.insufficient_evidence is True
    chat_fn.assert_not_called()
    assert "excluded: review_status=pending-review" in (
        result.trace["documents_considered"]["pend"]["reason"]
    )


def test_citation_of_ineligible_doc_flagged_invalid(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = _corpus(
        _doc("good", "wheat cattle feed"),
        _doc("pend", "wheat cattle feed", "pending-review"),
    )
    chat_fn = Mock(return_value="Answer. [good] [pend]")
    result = answer_question("wheat for cattle?", corpus, chat_fn=chat_fn)
    assert result.source_ids_supplied == ["good"]
    check = result.trace["citation_check"]
    assert check["contained"] is False
    assert check["invalid"] == ["pend"]


def test_clarification_retry_cannot_use_pending_evidence():
    from localevoice.knowledge.corpus import load_corpus
    from localevoice.pipeline.conversation import (
        AWAITING_CLARIFICATION,
        respond_to_clarification,
        start_conversation,
    )

    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "luzerne", corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    assert conv.evidence == []
    assert conv.result is not None
    assert conv.result.source_ids_supplied == []
    assert "feedipedia-alfalfa" not in (
        conv.result.trace["selected_evidence_ids"]
    )
    chat_fn.assert_not_called()


def test_real_corpus_alfalfa_excluded_but_visible():
    from localevoice.knowledge.corpus import load_corpus

    corpus = load_corpus("data/knowledge")
    assert "feedipedia-alfalfa" in corpus.ids  # not silently deleted
    chat_fn = Mock(return_value="must not be called")
    result = answer_question(
        "La luzerne est-elle un bon fourrage pour les vaches ?",
        corpus,
        chat_fn=chat_fn,
    )
    assert result.insufficient_evidence is True
    assert "feedipedia-alfalfa" not in result.source_ids_supplied
    chat_fn.assert_not_called()
    assert "excluded: review_status=pending-review" in (
        result.trace["documents_considered"]["feedipedia-alfalfa"]["reason"]
    )
