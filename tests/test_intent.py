"""Unit tests for deterministic intent classification. No network, no LLM.

The classifier is pure keyword rules. Notably: greeting requires ALL
tokens to be greeting tokens, so mixed messages fall through; Arabic
script alone implies nothing.
"""

from __future__ import annotations

import pytest

from localevoice.pipeline.intent import (
    AGRICULTURAL_QUESTION,
    GOODBYE,
    GREETING,
    THANKS,
    UNCLEAR,
    UNSUPPORTED_GENERAL,
    classify_intent,
)


@pytest.mark.parametrize(
    "text",
    [
        "السلام عليكم",
        "السلام عليكم ورحمة الله",
        "سلام",
        "صباح الخير",
        "مساء النور",
        "مرحبا بك",
        "bonjour",
        "hello",
    ],
)
def test_greetings(text):
    intent = classify_intent(text)
    assert intent.name == GREETING
    assert intent.response is not None
    assert "LocaleVoice" in intent.response


@pytest.mark.parametrize(
    "text", ["شكرا", "بارك الله فيك", "merci", "thanks"]
)
def test_thanks(text):
    intent = classify_intent(text)
    assert intent.name == THANKS
    assert intent.response is not None


@pytest.mark.parametrize("text", ["بسلامة", "bye", "au revoir"])
def test_goodbye(text):
    intent = classify_intent(text)
    assert intent.name == GOODBYE
    assert intent.response is not None


@pytest.mark.parametrize(
    "text",
    [
        "What is the capital of Morocco?",
        "شنو هي عاصمة المغرب؟",
        "من ربح في مباراة football؟",
    ],
)
def test_unsupported_general(text):
    intent = classify_intent(text)
    assert intent.name == UNSUPPORTED_GENERAL
    assert intent.response is not None


def test_agricultural_signal_detected():
    assert (
        classify_intent("Is wheat grain a good source of energy for cattle?").name
        == AGRICULTURAL_QUESTION
    )
    assert classify_intent("القمح واش مزيان للبقر؟").name == AGRICULTURAL_QUESTION


def test_mixed_greeting_and_question_falls_through():
    # "hello" plus real content must NOT resolve as a greeting.
    intent = classify_intent("hello, is wheat good for cattle?")
    assert intent.name == AGRICULTURAL_QUESTION
    assert intent.response is None


def test_arabic_script_alone_implies_nothing():
    intent = classify_intent("كلام غير مفهوم xyzzy")
    assert intent.name == UNCLEAR
    assert intent.response is None


def test_empty_and_blank_are_unclear():
    assert classify_intent("").name == UNCLEAR
    assert classify_intent("   ").name == UNCLEAR


def test_responses_carry_no_citations():
    from localevoice.pipeline.answer import find_citations
    from localevoice.pipeline.intent import RESPONSES

    for name, message in RESPONSES.items():
        assert find_citations(message) == [], name
        assert "[" not in message, name


def test_greeting_resolves_without_model_call():
    from unittest.mock import Mock

    from localevoice.knowledge.corpus import load_corpus
    from localevoice.pipeline.answer import answer_question

    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question("السلام عليكم", corpus, chat_fn=chat_fn)
    assert result.intent == GREETING
    assert result.insufficient_evidence is False
    assert result.model is None
    assert "مرحبا بك" in result.answer_text
    assert result.trace["model_called"] is False
    chat_fn.assert_not_called()


def test_thanks_resolves_without_model_call():
    from unittest.mock import Mock

    from localevoice.knowledge.corpus import load_corpus
    from localevoice.pipeline.answer import answer_question

    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    result = answer_question("شكرا", corpus, chat_fn=chat_fn)
    assert result.intent == THANKS
    assert result.insufficient_evidence is False
    chat_fn.assert_not_called()


def test_greeting_conversation_answers_immediately():
    from unittest.mock import Mock

    from localevoice.knowledge.corpus import load_corpus
    from localevoice.pipeline.conversation import ANSWERED, start_conversation

    corpus = load_corpus("data/knowledge")
    chat_fn = Mock(return_value="must not be called")
    conv = start_conversation("السلام عليكم", corpus, chat_fn=chat_fn)
    assert conv.status == ANSWERED
    assert conv.evidence == []
    chat_fn.assert_not_called()
