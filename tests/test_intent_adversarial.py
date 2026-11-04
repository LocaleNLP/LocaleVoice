"""Phase 2 (4E): adversarial intent routing.

Pins greeting/question mixing, code-switching, unrecognized text,
unsupported-domain boundaries, and the no-model-call guarantee for
social/unsupported intents. Chat calls mocked throughout.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from localevoice.knowledge.corpus import load_corpus
from localevoice.pipeline.answer import answer_question
from localevoice.pipeline.intent import (
    AGRICULTURAL_QUESTION,
    GOODBYE,
    GREETING,
    THANKS,
    UNCLEAR,
    UNSUPPORTED_GENERAL,
    classify_intent,
)


@pytest.fixture(scope="module")
def corpus():
    return load_corpus("data/knowledge")


STANDALONE_SOCIAL = [
    ("السلام عليكم", GREETING),
    ("سلام", GREETING),
    ("Salam", GREETING),
    ("Bonjour", GREETING),
    ("صباح الخير", GREETING),
    ("شكرا", THANKS),
    ("شكرا بزاف", THANKS),
    ("شكرا جزيلا", THANKS),
    ("merci", THANKS),
    ("بسلامة", GOODBYE),
]

MIXED_QUESTIONS = [
    "السلام عليكم، القمح واش مزيان للبقر؟",
    "شكرا، وشنو على الشعير للغنم؟",
    "Bonjour, le blé est-il bon pour les vaches?",
    "Salam, is wheat good for cattle?",
    "القمح واش مزيان؟ شكرا",
]

UNRECOGNIZED = [
    "bla bla xyz",
    "شكون نتا؟",
    "ممكن تعاوني؟",
    "بزاف",  # intensifier alone is not thanks
    "جزيلا",  # modifier alone is not thanks
    "تمام",
]


@pytest.mark.parametrize("text,expected", STANDALONE_SOCIAL)
def test_standalone_social_intents(text, expected):
    intent = classify_intent(text)
    assert intent.name == expected
    assert intent.response  # canned, no model needed


@pytest.mark.parametrize("text", MIXED_QUESTIONS)
def test_social_plus_question_reaches_retrieval(text):
    intent = classify_intent(text)
    assert intent.name == AGRICULTURAL_QUESTION
    assert intent.response is None


@pytest.mark.parametrize("text", UNRECOGNIZED)
def test_unrecognized_text_never_gets_canned_greeting(text):
    intent = classify_intent(text)
    assert intent.name == UNCLEAR
    assert intent.response is None


def test_ag_terms_absent_from_corpus_still_agricultural():
    # الدجاج البلدي has no corpus evidence but is clearly agricultural.
    intent = classify_intent("كيفاش نربي الدجاج البلدي؟")
    assert intent.name == AGRICULTURAL_QUESTION
    assert intent.response is None


@pytest.mark.parametrize(
    "text",
    [
        "What is the capital of Morocco?",
        "عاصمة المغرب شنو هي؟",
        "اشنو هي العاصمة ديال المغرب؟",
    ],
)
def test_unsupported_general_questions(text):
    intent = classify_intent(text)
    assert intent.name == UNSUPPORTED_GENERAL
    assert intent.response is not None


def test_unsupported_does_not_swallow_agricultural():
    # No unsupported trigger here: must flow to retrieval.
    intent = classify_intent("القمح واش مزيان للبقر فسوس؟")
    assert intent.name == AGRICULTURAL_QUESTION


@pytest.mark.parametrize(
    "text,name",
    [
        ("السلام عليكم", GREETING),
        ("شكرا بزاف", THANKS),
        ("What is the capital of Morocco?", UNSUPPORTED_GENERAL),
        ("القمح واش مزيان للبقر؟", AGRICULTURAL_QUESTION),
        ("شكون نتا؟", UNCLEAR),
    ],
)
def test_every_intent_appears_in_trace(corpus, text, name):
    chat_fn = Mock(return_value="must not be called")
    result = answer_question(text, corpus, chat_fn=chat_fn)
    assert result.intent == name
    assert result.trace is not None
    assert result.trace["detected_intent"] == name


@pytest.mark.parametrize(
    "text",
    ["السلام عليكم", "شكرا بزاف", "بسلامة", "عاصمة المغرب شنو هي؟"],
)
def test_social_and_unsupported_never_call_model(corpus, text):
    chat_fn = Mock(return_value="must not be called")
    result = answer_question(text, corpus, chat_fn=chat_fn)
    chat_fn.assert_not_called()
    assert result.model is None
