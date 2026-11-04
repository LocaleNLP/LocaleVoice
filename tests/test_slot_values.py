"""Phase 1 (4E): slot triggers vs recognized values vs unclassified terms.

Keyword triggers detect which KIND of context arrived; recognized values
identify actual user-supplied terms backed by the curated corpus; anything
else is unclassified -- never guessed. Chat calls mocked throughout.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from localevoice.knowledge.corpus import load_corpus
from localevoice.pipeline.clarify import (
    RECOGNIZED_CONFIDENCE,
    build_value_index,
    extract_context_slots,
    extract_slot_values,
)
from localevoice.pipeline.conversation import (
    ANSWERED,
    AWAITING_CLARIFICATION,
    respond_to_clarification,
    start_conversation,
)


@pytest.fixture(scope="module")
def corpus():
    return load_corpus("data/knowledge")


@pytest.fixture(scope="module")
def value_index(corpus):
    return build_value_index(corpus.documents)


# The ten realistic responses from the 4E spec: (response, slots,
# recognized original wordings, unclassified normalized terms).
SPEC_RESPONSES = [
    ("سوس ماسة", [], [], ["سوس", "ماسه"]),
    ("القمح", ["crop"], ["القمح"], []),
    ("هاد العام", ["season"], [], []),
    ("التربة رملية", ["soil"], [], []),
    ("الدودة فالطماطم", ["crop", "problem"], [], []),
    ("منطقة الغرب", ["location"], [], ["غرب"]),
    ("wheat", ["crop"], ["wheat"], []),
    ("olive trees", ["crop"], ["olive"], ["trees"]),
    ("this season", ["season"], [], []),
    ("sandy soil", ["soil"], [], ["sandy"]),
]


@pytest.mark.parametrize(
    "response,slots,words,unclassified", SPEC_RESPONSES
)
def test_spec_responses(value_index, response, slots, words, unclassified):
    assert extract_context_slots(response) == slots
    ext = extract_slot_values(response, value_index)
    assert [v.value for v in ext.values] == words
    assert list(ext.unclassified) == unclassified
    for value in ext.values:
        assert value.confidence == RECOGNIZED_CONFIDENCE
        assert value.matched_docs  # every value names its corpus backing


def test_wheat_value_matches_wheat_doc(value_index):
    ext = extract_slot_values("القمح", value_index)
    assert ext.values[0].matched_docs == ("feedipedia-wheat-grain",)


def test_olive_value_matches_olive_doc(value_index):
    ext = extract_slot_values("olive", value_index)
    assert ext.values[0].matched_docs == ("feedipedia-olive-cake",)


def test_slot_trigger_word_is_not_a_value(value_index):
    # "منطقة" names the slot; it is not itself a recognized value.
    ext = extract_slot_values("منطقة", value_index)
    assert extract_context_slots("منطقة") == ["location"]
    assert ext.values == ()
    assert list(ext.unclassified) == []


def test_unknown_value_is_not_marked_identified(value_index):
    # Proper nouns absent from the corpus must never gain an identity.
    ext = extract_slot_values("سوس ماسة", value_index)
    assert ext.values == ()
    assert set(ext.unclassified) == {"سوس", "ماسه"}


def test_unknown_differs_from_missing(value_index):
    # Unknown: terms present but unrecognized. Missing: nothing supplied.
    unknown = extract_slot_values("سوس ماسة", value_index)
    missing = extract_slot_values("", value_index)
    assert unknown.unclassified != ()
    assert missing.values == () and missing.unclassified == ()


def test_animal_slot_detected():
    assert extract_context_slots("علف للبقر") == ["animal"]
    assert extract_context_slots("عندي الغنم") == ["animal"]


def test_crop_and_animal_stay_distinct():
    assert extract_context_slots("القمح للبقر") == ["crop", "animal"]


def test_fused_prefixes_stem_but_real_words_survive():
    from localevoice.knowledge.retrieve import tokenize

    assert tokenize("فالطماطم") == ["طماطم"]
    assert tokenize("للغنم") == ["غنم"]
    assert tokenize("للبقر") == ["بقر"]
    assert tokenize("برسيم") == ["برسيم"]
    assert tokenize("فواكه") == ["فواكه"]
    assert tokenize("الفلاحة") == ["فلاحه"]


def test_values_and_terms_accumulate_across_turns(corpus):
    chat_fn = Mock(return_value="must not be called")
    conv = start_conversation(
        "شنو هي أحسن المزروعات فهاد المنطقة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "منطقة الغرب", corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    assert conv.slots_filled == ["location"]
    assert conv.slot_values == []
    assert conv.unclassified_terms == ["غرب"]
    record = conv.to_record()
    assert record["slot_values"] == []
    assert record["unclassified_terms"] == ["غرب"]


def test_recognized_value_accumulates_and_answers(monkeypatch, corpus):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    chat_fn = Mock(return_value="Answer. [feedipedia-wheat-grain]")
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    assert conv.status == ANSWERED
    assert conv.slots_filled == ["crop"]
    assert conv.slot_values == [
        {
            "value": "القمح",
            "slot": "crop",
            "confidence": RECOGNIZED_CONFIDENCE,
            "matched_docs": ["feedipedia-wheat-grain"],
        }
    ]
    assert conv.unclassified_terms == []


def test_error_rolls_back_values_and_terms(monkeypatch, corpus):
    from localevoice.providers.meta_chat import MetaChatError

    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    chat_fn = Mock(side_effect=MetaChatError("boom 503"))
    conv = start_conversation(
        "شحال كتسقي الزرع فالسيمانة؟", corpus, chat_fn=chat_fn
    )
    respond_to_clarification(conv, "القمح", corpus, chat_fn=chat_fn)
    assert conv.status == AWAITING_CLARIFICATION
    assert conv.slots_filled == []
    assert conv.slot_values == []
    assert conv.unclassified_terms == []
