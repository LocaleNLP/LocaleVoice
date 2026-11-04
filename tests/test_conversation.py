"""Regression tests for multi-turn clarification. Chat calls mocked."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from localevoice.knowledge.corpus import load_corpus
from localevoice.pipeline.answer import find_citations
from localevoice.pipeline.clarify import (
    CROP_MANAGEMENT,
    FARMER_DIAGNOSTIC,
    GENERIC,
    LOCATION_DEPENDENT,
    SOIL_CONTEXT,
    WEATHER_SEASONAL,
)
from localevoice.pipeline.conversation import (
    ABSTAINED,
    ANSWERED,
    AWAITING_CLARIFICATION,
    finish_conversation,
    respond_to_clarification,
    start_conversation,
)

FIVE = [
    ("شنو هي أحسن المزروعات فهاد المنطقة؟", LOCATION_DEPENDENT),
    ("كيفاش دايرة الحالة ديال الأرض هاد العام؟", SOIL_CONTEXT),
    ("واش التساقطات كانت كافية للموسم الفلاحي؟", WEATHER_SEASONAL),
    ("شحال كتسقي الزرع فالسيمانة؟", CROP_MANAGEMENT),
    ("شنو هي المشاكل لي كتعاني منها فالفلاحة؟", FARMER_DIAGNOSTIC),
]


@pytest.mark.parametrize("question,category", FIVE, ids=[c for _, c in FIVE])
def test_start_preserves_state_without_model_call(question, category):
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    conv = start_conversation(question, corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    assert conv.original_question == question
    assert conv.clarification_category == category
    assert len(conv.clarifications_asked) == 1
    assert conv.clarification_responses == []
    assert conv.accumulated_context == ""
    assert conv.evidence == []
    assert [t.role for t in conv.turns] == ["farmer", "assistant"]
    chat_fn.assert_not_called()
    assert find_citations(conv.turns[1].text) == []


def test_start_with_evidence_answers_immediately(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="Answer. [feedipedia-wheat-grain]")
    conv = start_conversation("القمح واش مزيان للبقر؟", corpus, chat_fn=chat_fn)
    assert conv.status == ANSWERED
    assert conv.evidence[0]["document_id"] == "feedipedia-wheat-grain"
    assert conv.clarifications_asked == []
    chat_fn.assert_called_once()


def test_start_generic_abstains_immediately():
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    conv = start_conversation("شنو هي عاصمة المغرب؟", corpus, chat_fn=chat_fn)
    assert conv.status == ABSTAINED
    assert conv.clarification_category == GENERIC
    chat_fn.assert_not_called()


def test_start_empty_question_rejected():
    corpus = load_corpus("data/knowledge")
    with pytest.raises(ValueError, match="non-empty"):
        start_conversation("   ", corpus)


def test_response_retrieves_with_original_plus_context(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="Answer. [feedipedia-wheat-grain]")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    assert conv.status == ANSWERED
    assert conv.original_question == "شحال كتسقي الزرع فالسيمانة؟"
    assert conv.clarification_responses == ["القمح"]
    assert "القمح" in conv.accumulated_context
    assert conv.evidence[0]["document_id"] == "feedipedia-wheat-grain"
    (messages_arg,), _ = chat_fn.call_args
    combined = messages_arg[1]["content"]
    assert "شحال كتسقي الزرع فالسيمانة؟" in combined
    assert "القمح" in combined


def test_response_without_evidence_stays_open_without_model_call():
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "الخضرة", corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    assert conv.evidence == []
    assert len(conv.clarifications_asked) == 2
    assert find_citations(conv.turns[-1].text) == []
    chat_fn.assert_not_called()


def test_multiple_responses_accumulate_then_answer(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="Answer. [feedipedia-wheat-grain]")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "الخضرة", corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    assert conv.status == ANSWERED
    assert conv.clarification_responses == ["الخضرة", "القمح"]
    assert "الخضرة" in conv.accumulated_context
    assert "القمح" in conv.accumulated_context
    assert chat_fn.call_count == 1


def test_finish_closes_open_conversation():
    corpus = load_corpus("data/knowledge")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=Mock()
    )
    finish_conversation(conv)
    assert conv.status == ABSTAINED
    finish_conversation(conv)  # idempotent
    assert conv.status == ABSTAINED


def test_restart_starts_fresh_conversation():
    corpus = load_corpus("data/knowledge")
    first = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=Mock()
    )
    respond_to_clarification(first, "الخضرة", corpus, chat_fn=Mock())
    second = start_conversation("شنو هي عاصمة المغرب؟", corpus, chat_fn=Mock())
    assert second.conversation_id != first.conversation_id
    assert second.original_question == "شنو هي عاصمة المغرب؟"
    assert second.clarification_responses == []
    assert first.clarification_responses == ["الخضرة"]  # untouched


def test_empty_response_rejected_without_state_change():
    corpus = load_corpus("data/knowledge")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=Mock()
    )
    before = len(conv.turns)
    with pytest.raises(ValueError, match="empty"):
        respond_to_clarification(conv, "   ", corpus, chat_fn=Mock())
    assert len(conv.turns) == before
    assert conv.clarification_responses == []
    assert conv.status == AWAITING_CLARIFICATION


def test_response_to_closed_conversation_rejected():
    corpus = load_corpus("data/knowledge")
    conv = start_conversation("شنو هي عاصمة المغرب؟", corpus, chat_fn=Mock())
    assert conv.status == ABSTAINED
    with pytest.raises(ValueError, match="start a new one"):
        respond_to_clarification(conv, "الرباط", corpus, chat_fn=Mock())


def test_error_result_rolls_back_turn(monkeypatch):
    from localevoice.providers.meta_chat import MetaChatError

    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(side_effect=MetaChatError("boom 503"))
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    assert conv.clarification_responses == []
    assert [t.role for t in conv.turns] == ["farmer", "assistant"]
    assert conv.result is not None and conv.result.error is not None


def test_failed_retries_never_duplicate_state(monkeypatch):
    # Integrity: fail twice, then succeed. Turns, responses, and context
    # must each contain the single response exactly once.
    from localevoice.providers.meta_chat import MetaChatError

    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(
        side_effect=[
            MetaChatError("boom 503"),
            MetaChatError("boom 503"),
            "Answer. [feedipedia-wheat-grain]",
        ]
    )
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    assert [t.role for t in conv.turns] == ["farmer", "assistant"]
    assert conv.clarification_responses == []
    assert conv.accumulated_context == ""
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    assert conv.status == ANSWERED
    assert [t.role for t in conv.turns] == ["farmer", "assistant", "farmer", "assistant"]
    assert conv.clarification_responses == ["القمح"]
    assert conv.accumulated_context == "القمح"
    assert chat_fn.call_count == 3


def test_response_to_answered_conversation_rejected(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="Answer. [feedipedia-wheat-grain]")
    conv = start_conversation("القمح واش مزيان للبقر؟", corpus, chat_fn=chat_fn)
    assert conv.status == ANSWERED
    with pytest.raises(ValueError, match="start a new one"):
        respond_to_clarification(conv, "شكرا", corpus, chat_fn=chat_fn)
    assert len(conv.turns) == 2


def test_conversation_record_has_no_secrets(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "super-secret-key")
    corpus = load_corpus("data/knowledge")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=Mock()
    )
    blob = str(conv.to_record())
    assert "super-secret-key" not in blob
    assert "MODEL_API_KEY" not in blob
    assert conv.to_record()["original_question"].startswith("شحال")
