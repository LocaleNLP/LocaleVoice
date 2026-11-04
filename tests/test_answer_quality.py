"""Answer-quality evaluation suite (Milestone 6C, cases A-L).

Mocked-model wiring tests: each case records retrieved evidence,
eligible evidence, model invocation, generated answer, citation
validation, abstention decision, and expected-vs-actual outcome.
Mocks prove pipeline wiring only — prompt compliance by the real
model needs live evaluation, and Darija naturalness needs humans.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from localevoice.knowledge.corpus import Corpus, Document, load_corpus
from localevoice.pipeline.answer import answer_question
from localevoice.pipeline.conversation import (
    respond_to_clarification,
    start_conversation,
)


@pytest.fixture(scope="module")
def corpus():
    return load_corpus("data/knowledge")


@pytest.fixture(autouse=True)
def _model_env(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")


def _doc(doc_id, text, title="T"):
    return Document(
        id=doc_id,
        title=title,
        source_name="P",
        source_url="https://example.org",
        category="Cereals",
        crop_or_species="wheat",
        excerpt=text,
        language="en",
        date_accessed="2026-10-29",
        review_status="verified-excerpt",
    )


def _olive_only_corpus():
    return Corpus(
        documents=[
            _doc(
                "feedipedia-olive-cake",
                "Olive cake is fed to ruminants including cattle.",
                title="Olive oil cake",
            )
        ],
        manifest={},
        corpus_dir="test",
    )


def _wheat_only_corpus():
    return Corpus(
        documents=[
            _doc(
                "feedipedia-wheat-grain",
                "Wheat is an energy source for ruminants.",
                title="Wheat grain",
            )
        ],
        manifest={},
        corpus_dir="test",
    )


def _run(question, corpus, mock_answer):
    """Run one case; return the recorded evaluation fields."""
    chat_fn = Mock(return_value=mock_answer)
    result = answer_question(question, corpus, chat_fn=chat_fn)
    check = (result.trace or {}).get("citation_check") or {}
    return {
        "retrieved": [e["document_id"] for e in result.evidence],
        "eligible": list(result.source_ids_supplied),
        "model_invoked": chat_fn.called,
        "answer": result.answer_text,
        "citations": {
            "found": check.get("found", []),
            "invalid": check.get("invalid", []),
            "malformed": check.get("malformed", []),
            "contained": check.get("contained"),
            "syntax_ok": check.get("syntax_ok"),
        },
        "hygiene": ((result.trace or {}).get("hygiene") or {}),
        "abstained": result.insufficient_evidence,
        "actual": (
            "abstain"
            if result.insufficient_evidence
            else ("error" if result.error else "answer")
        ),
    }


def test_case_a_relevant_wheat_evidence(corpus):
    record = _run(
        "القمح واش مزيان للبقر؟",
        corpus,
        "القمح مزيان للبقر. [feedipedia-wheat-grain]",
    )
    assert record["retrieved"] == ["feedipedia-wheat-grain"]
    assert record["model_invoked"] is True
    assert record["citations"]["contained"] is True
    assert record["citations"]["syntax_ok"] is True
    assert record["abstained"] is False
    assert record["actual"] == "answer"  # expected: answer


def test_case_b_olive_cake_evidence(corpus):
    record = _run(
        "واش tourteau d'olive مزيان للغنم؟",
        corpus,
        "مزيان للغنم. [feedipedia-olive-cake]",
    )
    assert record["retrieved"] == ["feedipedia-olive-cake"]
    assert record["model_invoked"] is True
    assert record["citations"]["contained"] is True
    assert record["actual"] == "answer"  # expected: answer


def test_case_c_wheat_question_with_only_olive_evidence():
    corpus = _olive_only_corpus()
    record = _run(
        "Is wheat good for cattle?",
        corpus,
        "الدليل كيهضر على tourteau للبقر، ماشي على القمح. "
        "[feedipedia-olive-cake]",
    )
    assert record["retrieved"] == ["feedipedia-olive-cake"]
    assert record["model_invoked"] is True  # compliant mock scopes honestly
    assert record["citations"]["contained"] is True
    assert record["actual"] == "answer"  # expected: scoped answer


def test_case_c2_containment_is_not_claim_verification():
    # Limitation made explicit: a non-compliant model CAN cite wheat
    # claims to the olive passage and still pass containment.
    # Deterministic code cannot verify claim semantics (see docs/18).
    corpus = _olive_only_corpus()
    record = _run(
        "Is wheat good for cattle?",
        corpus,
        "Wheat is excellent for cattle. [feedipedia-olive-cake]",
    )
    assert record["citations"]["contained"] is True
    assert record["actual"] == "answer"


def test_case_d_soil_question_without_soil_evidence(corpus):
    record = _run(
        "What type of soil is best for tomatoes in Morocco?",
        corpus,
        "must not be called",
    )
    assert record["retrieved"] == []
    assert record["model_invoked"] is False
    assert record["abstained"] is True
    assert record["actual"] == "abstain"  # expected: clarify/abstain


def test_case_e_mixed_question_incomplete_evidence():
    corpus = _wheat_only_corpus()
    record = _run(
        "Compare wheat and olive cake for cattle.",
        corpus,
        "Wheat is an energy source. [feedipedia-wheat-grain] "
        "The evidence does not cover olive cake.",
    )
    assert record["retrieved"] == ["feedipedia-wheat-grain"]
    assert record["model_invoked"] is True
    assert record["citations"]["contained"] is True
    assert "olive cake" in record["answer"]  # uncovered part named
    assert record["actual"] == "answer"  # expected: partial answer


def test_case_f_unsupported_crop(corpus):
    record = _run("How do I grow tomatoes?", corpus, "must not be called")
    assert record["retrieved"] == []
    assert record["model_invoked"] is False
    assert record["actual"] == "abstain"  # expected: abstain


def test_case_g_multi_topic_question(corpus):
    record = _run(
        "Is wheat good for cattle, and was rainfall enough this season?",
        corpus,
        "Wheat is an energy source. [feedipedia-wheat-grain] "
        "Rainfall is not covered by the evidence.",
    )
    assert "feedipedia-wheat-grain" in record["retrieved"]
    assert record["model_invoked"] is True
    assert record["actual"] == "answer"  # expected: wheat part only


def test_case_h_malformed_citation_response(corpus):
    record = _run(
        "القمح واش مزيان للبقر؟",
        corpus,
        "مزيان olive-cake] بزاف. [feedipedia-wheat-grain]",
    )
    assert record["citations"]["malformed"] == ["olive-cake]"]
    assert record["citations"]["syntax_ok"] is False
    assert record["actual"] == "answer"  # expected: flagged, not silent


def test_case_i_unknown_citation_ids(corpus):
    record = _run(
        "القمح واش مزيان للبقر؟",
        corpus,
        "مزيان. [feedipedia-rice]",
    )
    assert record["citations"]["invalid"] == ["feedipedia-rice"]
    assert record["citations"]["contained"] is False
    assert record["actual"] == "answer"  # expected: flagged invalid


def test_case_j_english_fragments_in_arabic(corpus):
    record = _run(
        "القمح واش مزيان للبقر؟",
        corpus,
        "القمح seres مهم. [feedipedia-wheat-grain]",
    )
    assert "seres" in record["hygiene"]["latin_fragments"]
    assert record["hygiene"]["clean"] is False
    assert record["actual"] == "answer"  # expected: flagged, advisory


def test_case_k_repeated_sentences(corpus):
    record = _run(
        "القمح واش مزيان للبقر؟",
        corpus,
        "القمح مزيان للبقر بزاف. القمح مزيان للبقر بزاف. "
        "[feedipedia-wheat-grain]",
    )
    assert record["hygiene"]["repeated_sentences"] == [
        "القمح مزيان للبقر بزاف"
    ]
    assert record["actual"] == "answer"  # expected: flagged, advisory


def test_case_l_clarification_then_unsupported(corpus):
    chat_fn = Mock(return_value="must not be called")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(
        conv, "What is the capital of Morocco?", corpus, chat_fn=chat_fn
    )
    assert conv.evidence == []
    assert conv.result is not None
    assert conv.result.source_ids_supplied == []
    assert conv.result.insufficient_evidence is True
    chat_fn.assert_not_called()  # expected: no model call, stays open
