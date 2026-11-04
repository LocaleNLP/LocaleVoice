"""Reproducible live answer evaluation (Milestone 6D).

Runs versioned cases through the real answer pipeline with a caller-
supplied chat function (the script wires the live Meta provider).
Every case records retrieval, eligibility, invocation, raw answer,
citation validation, hygiene, outcome, latency, and error — plus
the full trace the offline runner drops. Nothing is fabricated;
unmeasurable axes are reported as NOT MEASURED, never zero.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from localevoice.knowledge.corpus import Corpus
from localevoice.knowledge.retrieve import retrieve
from localevoice.pipeline.answer import answer_question

NOT_MEASURED = "NOT MEASURED"
HUMAN_REVIEW_PENDING = "PENDING"


@dataclass
class LiveCase:
    id: str
    section: str
    question: str
    intended_meaning: str
    expected_evidence_ids: list[str]
    expected_outcome: str  # answer | abstain | scoped | clarify
    notes: str = ""


@dataclass
class LiveCaseReport:
    case_id: str
    section: str
    question: str
    language_inferred: str | None
    intent: str | None
    retrieved_ids: list[str]
    eligible_ids: list[str]
    supplied_ids: list[str]
    model_called: bool
    raw_response: str | None
    parsed_citations: list[str] = field(default_factory=list)
    citation_syntax: dict = field(default_factory=dict)
    citation_containment: dict = field(default_factory=dict)
    hygiene: dict = field(default_factory=dict)
    outcome: str = "error"  # answer | clarify | abstain | unsupported | error
    latency_ms: int | None = None
    error: dict | None = None
    trace: dict | None = None
    expected_outcome: str = ""
    outcome_match: bool | None = None
    claim_support: str = NOT_MEASURED
    human_review: str = HUMAN_REVIEW_PENDING


def load_live_cases(path: str) -> tuple[dict, list[LiveCase]]:
    """Load live cases; return (metadata, cases)."""
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict) or not isinstance(
        payload.get("cases"), list
    ):
        raise ValueError("live cases file must be an object with cases list")
    cases = []
    for raw in payload["cases"]:
        for name in (
            "id",
            "section",
            "question",
            "intended_meaning",
            "expected_evidence_ids",
            "expected_outcome",
        ):
            if name not in raw:
                raise ValueError(f"live case missing field: {name}")
        cases.append(
            LiveCase(
                id=raw["id"],
                section=raw["section"],
                question=raw["question"],
                intended_meaning=raw["intended_meaning"],
                expected_evidence_ids=list(raw["expected_evidence_ids"]),
                expected_outcome=raw["expected_outcome"],
                notes=raw.get("notes", ""),
            )
        )
    metadata = {k: v for k, v in payload.items() if k != "cases"}
    return metadata, cases


def _outcome_of(result) -> str:
    if result.error:
        return "error"
    if result.intent == "unsupported_general_question":
        return "unsupported"
    if not result.insufficient_evidence:
        return "answer"
    if result.clarification_category and result.clarification_category != "generic":
        return "clarify"
    return "abstain"


def evaluate_live_case(
    case: LiveCase,
    corpus: Corpus,
    chat_fn: Callable[..., str],
    *,
    top_k: int = 3,
    min_score: int = 1,
    timeout: float = 90.0,
) -> LiveCaseReport:
    """Run one case through the real pipeline. One model call at most."""
    raw_ranking = retrieve(case.question, corpus.documents, top_k=top_k)
    result = answer_question(
        case.question,
        corpus,
        top_k=top_k,
        min_score=min_score,
        chat_fn=chat_fn,
        timeout=timeout,
    )
    trace = result.trace or {}
    check = trace.get("citation_check") or {}
    outcome = _outcome_of(result)
    return LiveCaseReport(
        case_id=case.id,
        section=case.section,
        question=case.question,
        language_inferred=result.language.inferred if result.language else None,
        intent=result.intent,
        retrieved_ids=[e.document_id for e in raw_ranking if e.score >= min_score],
        eligible_ids=list(result.source_ids_supplied),
        supplied_ids=list(result.source_ids_supplied),
        model_called=bool(trace.get("model_called", False)),
        raw_response=result.answer_text,
        parsed_citations=list(check.get("found", [])),
        citation_syntax={
            "syntax_ok": check.get("syntax_ok"),
            "malformed": list(check.get("malformed", [])),
        },
        citation_containment={
            "contained": check.get("contained"),
            "invalid": list(check.get("invalid", [])),
        },
        hygiene=dict(trace.get("hygiene") or {}),
        outcome=outcome,
        latency_ms=result.elapsed_ms,
        error=result.error,
        trace=trace,
        expected_outcome=case.expected_outcome,
        outcome_match=(
            outcome == case.expected_outcome
            if case.expected_outcome != "scoped"
            else (outcome == "answer")
        ),
    )


def summarize_live(reports: list[LiveCaseReport]) -> dict:
    """Aggregate without hiding failures: counts plus per-case flags."""
    return {
        "total": len(reports),
        "model_calls": sum(1 for r in reports if r.model_called),
        "outcomes": {
            name: sum(1 for r in reports if r.outcome == name)
            for name in ("answer", "clarify", "abstain", "unsupported", "error")
        },
        "outcome_match": sum(1 for r in reports if r.outcome_match),
        "syntax_ok": sum(
            1 for r in reports if r.citation_syntax.get("syntax_ok") is True
        ),
        "syntax_failed": [
            r.case_id for r in reports if r.citation_syntax.get("syntax_ok") is False
        ],
        "containment_ok": sum(
            1
            for r in reports
            if r.citation_containment.get("contained") is True
        ),
        "containment_failed": [
            r.case_id
            for r in reports
            if r.citation_containment.get("contained") is False
        ],
        "hygiene_clean": sum(
            1 for r in reports if r.hygiene.get("clean") is True
        ),
        "hygiene_flagged": [
            r.case_id for r in reports if r.hygiene.get("clean") is False
        ],
        "claim_support": NOT_MEASURED,
        "human_naturalness": NOT_MEASURED,
        "errors": sum(1 for r in reports if r.error),
    }


def write_live_report(
    path: str, metadata: dict, reports: list[LiveCaseReport]
) -> None:
    """Write a JSON live-evaluation report. Contains no API keys."""
    payload = {
        "metadata": metadata,
        "summary": summarize_live(reports),
        "cases": [asdict(r) for r in reports],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
