"""Phase 4 (4E): the 20-question benchmark set stays green.

Loads data/evaluation/questions_4e.json and asserts every documented
expectation: retrieval recall, the insufficient-evidence gate, intent,
clarification category, model-call discipline, and final outcome.
Chat calls mocked; the mock asserts citation discipline, not wording.
"""

from __future__ import annotations

import json
import os
from unittest.mock import Mock

import pytest

from localevoice.evaluation.runner import load_fixtures
from localevoice.knowledge.corpus import is_answer_eligible, load_corpus
from localevoice.knowledge.retrieve import retrieve
from localevoice.pipeline.answer import answer_question, find_citations

FIXTURES = os.path.join(
    os.path.dirname(__file__), "..", "data", "evaluation", "questions_4e.json"
)
GENERIC = "generic"


@pytest.fixture(scope="module")
def corpus():
    return load_corpus("data/knowledge")


@pytest.fixture(scope="module")
def raw_items():
    with open(FIXTURES, encoding="utf-8") as fh:
        return json.load(fh)["items"]


def outcome_of(result) -> str:
    if result.intent == "greeting":
        return "greeting"
    if result.intent == "unsupported_general_question":
        return "unsupported"
    if not result.insufficient_evidence:
        return "answer"
    if result.clarification_category and result.clarification_category != GENERIC:
        return "clarification"
    return "abstain"


def test_set_has_twenty_items(raw_items):
    assert len(raw_items) == 20
    assert len({it["id"] for it in raw_items}) == 20


def _eligible_retrieved(corpus, question):
    # Same eligibility-aware view as the runner and the pipeline (5.1):
    # pending-review matches never count as retrieved evidence.
    eligible = {d.id for d in corpus.documents if is_answer_eligible(d)}
    found = retrieve(question, corpus.documents, top_k=3)
    return [e.document_id for e in found if e.score >= 1 and e.document_id in eligible]


def test_offline_recall_and_gating(corpus, raw_items):
    for it in raw_items:
        retrieved = _eligible_retrieved(corpus, it["question"])
        assert set(it["relevant_doc_ids"]) <= set(retrieved), it["id"]
        assert (not retrieved) == it["expect_insufficient"], it["id"]


def test_multi_doc_items_retrieve_both(corpus, raw_items):
    multi = [it for it in raw_items if it["category"] == "multi-doc"]
    assert len(multi) == 2
    for it in multi:
        retrieved = set(_eligible_retrieved(corpus, it["question"]))
        assert set(it["relevant_doc_ids"]) <= retrieved, it["id"]


def test_pipeline_expectations(monkeypatch, corpus, raw_items):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    for it in raw_items:
        cited = "".join(f"[{d}]" for d in it["relevant_doc_ids"])
        chat_fn = Mock(return_value=f"Mock answer. {cited}")
        result = answer_question(it["question"], corpus, chat_fn=chat_fn)
        assert result.intent == it["expected_intent"], it["id"]
        assert result.clarification_category == it["expect_clarification"], it["id"]
        assert chat_fn.called == it["expect_model_call"], it["id"]
        assert outcome_of(result) == it["expected_outcome"], it["id"]
        if it["expect_model_call"]:
            assert result.error is None, it["id"]
            for citation in find_citations(result.answer_text):
                assert citation in result.source_ids_supplied, it["id"]


def test_fixtures_load_through_runner():
    metadata, fixtures = load_fixtures(FIXTURES)
    assert metadata["fixtures_version"] == "m4e-eval-1.1.0"
    assert len(fixtures) == 20
