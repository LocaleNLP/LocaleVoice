"""Unit tests for the live evaluator (Milestone 6D). All mocked.

The live script itself is exercised only via --dry-run (subprocess,
no provider). Live provider behavior is measured by real runs whose
reports land under data/evaluation/live/, never by these tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from unittest.mock import Mock

import pytest

from localevoice.evaluation.live import (
    NOT_MEASURED,
    LiveCase,
    evaluate_live_case,
    load_live_cases,
    summarize_live,
    write_live_report,
)
from localevoice.knowledge.corpus import load_corpus
from localevoice.providers.meta_chat import MetaChatError

CASES = os.path.join(
    os.path.dirname(__file__), "..", "data", "evaluation", "live_cases_6d.json"
)
SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "evaluate_live_answers.py")


@pytest.fixture(scope="module")
def corpus():
    return load_corpus("data/knowledge")


@pytest.fixture(scope="module")
def cases():
    _, items = load_live_cases(CASES)
    return {c.id: c for c in items}


@pytest.fixture(autouse=True)
def _model_env(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")


def test_fifteen_cases_load_with_documented_intent(cases):
    assert len(cases) == 15
    for case in cases.values():
        assert case.question.strip()
        assert case.intended_meaning.strip()
        assert case.expected_outcome in ("answer", "abstain", "scoped", "clarify")


def test_dry_run_lists_cases_without_provider_calls():
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--dry-run"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0
    assert "0 provider calls" in proc.stdout
    assert "L01-wheat-nutrition" in proc.stdout
    assert "L15-darija-multi" in proc.stdout


def test_dry_run_rejects_unknown_case_filter():
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--dry-run", "--case", "nope"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 1


def test_evaluate_case_records_all_stages(corpus, cases):
    chat_fn = Mock(return_value="Wheat is good. [feedipedia-wheat-grain]")
    report = evaluate_live_case(cases["L12-citation-integrity"], corpus, chat_fn)
    assert report.retrieved_ids  # raw ranking recorded
    # L12 over-retrieves olive via "ruminants" (6D relevance finding):
    # both eligible docs are honestly recorded as supplied.
    assert report.eligible_ids == [
        "feedipedia-wheat-grain",
        "feedipedia-olive-cake",
    ]
    assert report.supplied_ids == report.eligible_ids
    assert report.model_called is True
    assert report.raw_response.startswith("Wheat is good.")
    assert report.parsed_citations == ["feedipedia-wheat-grain"]
    assert report.citation_syntax["syntax_ok"] is True
    assert report.citation_containment["contained"] is True
    assert report.hygiene["clean"] is True
    assert report.outcome == "answer"
    assert report.outcome_match is True
    assert report.latency_ms is not None
    assert report.trace is not None  # full trace kept (offline runner drops it)
    assert report.claim_support == NOT_MEASURED
    assert report.human_review == "PENDING"


def test_abstain_case_makes_no_model_call(corpus, cases):
    chat_fn = Mock(return_value="must not be called")
    report = evaluate_live_case(cases["L06-tomato-no-evidence"], corpus, chat_fn)
    chat_fn.assert_not_called()
    assert report.model_called is False
    assert report.outcome == "abstain"
    assert report.outcome_match is True


def test_ineligible_docs_excluded_from_supplied(corpus, cases):
    chat_fn = Mock(return_value="Wheat only. [feedipedia-wheat-grain]")
    report = evaluate_live_case(cases["L10-multi-feed-soil"], corpus, chat_fn)
    assert "feedipedia-alfalfa" in report.retrieved_ids  # visible in raw ranking
    assert "feedipedia-alfalfa" not in report.eligible_ids
    assert "feedipedia-alfalfa" not in report.supplied_ids


def test_provider_error_recorded_not_raised(corpus, cases):
    chat_fn = Mock(side_effect=MetaChatError("boom 503"))
    report = evaluate_live_case(cases["L01-wheat-nutrition"], corpus, chat_fn)
    assert report.outcome == "error"
    assert report.error is not None
    assert report.error["type"] == "MetaChatError"
    assert report.outcome_match is False


def test_malformed_citations_summarized_per_case(corpus, cases):
    chat_fn = Mock(return_value="Good olive-cake] wheat.")
    report = evaluate_live_case(cases["L03-olive-cake-feed"], corpus, chat_fn)
    assert report.citation_syntax["syntax_ok"] is False
    summary = summarize_live([report])
    assert summary["syntax_failed"] == ["L03-olive-cake-feed"]
    assert summary["syntax_ok"] == 0


def test_summary_marks_unmeasured_axes(corpus, cases):
    chat_fn = Mock(return_value="Fine. [feedipedia-wheat-grain]")
    report = evaluate_live_case(cases["L01-wheat-nutrition"], corpus, chat_fn)
    summary = summarize_live([report])
    assert summary["claim_support"] == NOT_MEASURED
    assert summary["human_naturalness"] == NOT_MEASURED
    assert summary["total"] == 1
    assert "outcomes" in summary


def test_report_serializes_without_secrets(monkeypatch, tmp_path, corpus, cases):
    monkeypatch.setenv("MODEL_API_KEY", "super-secret-key")
    chat_fn = Mock(return_value="Fine. [feedipedia-wheat-grain]")
    report = evaluate_live_case(cases["L01-wheat-nutrition"], corpus, chat_fn)
    out = str(tmp_path / "live.json")
    write_live_report(out, {"mode": "live"}, [report])
    payload = json.load(open(out, encoding="utf-8"))
    dumped = json.dumps(payload)
    assert "super-secret-key" not in dumped
    assert "Bearer" not in dumped
    assert payload["cases"][0]["human_review"] == "PENDING"
