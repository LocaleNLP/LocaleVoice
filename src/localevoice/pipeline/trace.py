"""Evidence-trace construction and citation validation (Milestone 4D).

A trace explains, for one question, why evidence was or was not
selected — without reading source code and without secrets. Traces are
pure data built from values the pipeline already computed.

Important distinction: citation containment (every [id] in the answer
appears in the supplied IDs) is NOT independent factual verification.
It proves the model cited only given sources, not that each generated
statement is true. The trace reports containment only and never claims
more.
"""

from __future__ import annotations

import re

_CITATION = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9._-]*)\]")


def find_citations(answer_text: str) -> list[str]:
    """Extract [source-id] citations from generated text."""
    return _CITATION.findall(answer_text)


def validate_citations(answer_text: str, supplied_ids: list[str]) -> dict:
    """Check cited IDs against supplied IDs. Pure; never mutates text."""
    found = find_citations(answer_text)
    supplied = set(supplied_ids)
    invalid = sorted({c for c in found if c not in supplied})
    return {
        "found": found,
        "supplied": list(supplied_ids),
        "contained": not invalid,
        "invalid": invalid,
    }


def build_trace(
    *,
    question: str,
    normalized_question: str,
    intent: str,
    category: str | None,
    keywords: list[str],
    considered: dict[str, dict],
    selected_ids: list[str],
    min_score: float,
    top_k: int,
    sufficient: bool,
    clarification_requested: bool,
    model_called: bool,
    model_id: str | None,
    citation_check: dict | None,
    status: str,
    error_type: str | None = None,
) -> dict:
    """Assemble the evidence trace. `considered` maps doc id to
    {"score": float, "matched": [...], "selected": bool, "reason": str}."""
    return {
        "question": question,
        "normalized_question": normalized_question,
        "detected_intent": intent,
        "detected_category": category,
        "extracted_keywords": keywords,
        "documents_considered": considered,
        "selected_evidence_ids": selected_ids,
        "thresholds": {"min_score": min_score, "top_k": top_k},
        "sufficient_evidence": sufficient,
        "clarification_requested": clarification_requested,
        "model_called": model_called,
        "model_id": model_id,
        "citation_check": citation_check,
        "status": status,
        "error_type": error_type,
    }
