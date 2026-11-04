"""Regression tests: Darija no-evidence questions get clarifications.

All five diagnostic questions retrieve nothing from the verified corpus,
so the pipeline must abstain (no model call, no citations) while
returning a targeted clarification instead of the generic rejection.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from localevoice.knowledge.corpus import load_corpus
from localevoice.pipeline.answer import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    answer_question,
    find_citations,
)
from localevoice.pipeline.clarify import (
    CROP_MANAGEMENT,
    FARMER_DIAGNOSTIC,
    GENERIC,
    LOCATION_DEPENDENT,
    MESSAGES,
    SOIL_CONTEXT,
    WEATHER_SEASONAL,
    classify_question,
)

FIVE_QUESTIONS = [
    ("شنو هي أحسن المزروعات فهاد المنطقة؟", LOCATION_DEPENDENT, "إقليم"),
    ("كيفاش دايرة الحالة ديال الأرض هاد العام؟", SOIL_CONTEXT, "التربة"),
    ("واش التساقطات كانت كافية للموسم الفلاحي؟", WEATHER_SEASONAL, "موسم"),
    ("شحال كتسقي الزرع فالسيمانة؟", CROP_MANAGEMENT, "المزروعات"),
    ("شنو هي المشاكل لي كتعاني منها فالفلاحة؟", FARMER_DIAGNOSTIC, "المشكل"),
]


@pytest.mark.parametrize(
    "question,category,keyword", FIVE_QUESTIONS, ids=[c for _, c, _ in FIVE_QUESTIONS]
)
def test_diagnostic_questions_get_targeted_clarification(
    question, category, keyword
):
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question(question, corpus, chat_fn=chat_fn)
    assert result.insufficient_evidence is True
    assert result.clarification_category == category
    assert keyword in result.answer_text
    assert result.evidence == []
    assert result.source_ids_supplied == []
    assert result.model is None
    chat_fn.assert_not_called()
    assert find_citations(result.answer_text) == []


def test_classify_question_direct_categories():
    assert classify_question("شنو هي عاصمة المغرب؟").category == GENERIC
    assert classify_question("شنو هي عاصمة المغرب؟").message is None
    assert (
        classify_question("combien irriguer par semaine ?").category
        == CROP_MANAGEMENT
    )
    assert classify_question("parle-moi de la pluie").category == WEATHER_SEASONAL
    assert classify_question("").category == GENERIC


def test_evidence_available_still_answers_without_clarification(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="Answer. [feedipedia-wheat-grain]")
    result = answer_question("القمح واش مزيان للبقر؟", corpus, chat_fn=chat_fn)
    assert result.insufficient_evidence is False
    assert result.clarification_category is None
    assert result.source_ids_supplied == ["feedipedia-wheat-grain"]
    chat_fn.assert_called_once()


def test_unsupported_question_gets_domain_response():
    # Deliberate 4D change: clear out-of-domain questions get the
    # unsupported-domain message instead of the generic abstention.
    from localevoice.pipeline.intent import RESPONSES, UNSUPPORTED_GENERAL

    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question("شنو هي عاصمة المغرب؟", corpus, chat_fn=chat_fn)
    assert result.insufficient_evidence is True
    assert result.intent == UNSUPPORTED_GENERAL
    assert result.answer_text == RESPONSES[UNSUPPORTED_GENERAL]
    assert result.evidence == []
    chat_fn.assert_not_called()


def test_truly_unknown_question_keeps_generic_abstention():
    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question("كلام غير مفهوم xyzzy", corpus, chat_fn=chat_fn)
    assert result.insufficient_evidence is True
    assert result.clarification_category == GENERIC
    assert result.answer_text == INSUFFICIENT_EVIDENCE_MESSAGE
    chat_fn.assert_not_called()


def test_no_clarification_message_contains_citations_or_claims():
    for category, message in MESSAGES.items():
        assert find_citations(message) == [], category
        assert "[" not in message and "]" not in message, category
