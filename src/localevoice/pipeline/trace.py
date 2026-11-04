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

# Citation-like fragments that are NOT valid citations: a dangling
# "id]" with no opening bracket, an unclosed "[id" at end of text,
# brackets containing spaces, and empty brackets. These are invisible
# to find_citations, so without this check a truncated citation such
# as "olive-cake]" would pass containment while rendering as garbage.
_DANGLING_CLOSE = re.compile(
    r"(?<!\[)(?<![A-Za-z0-9._-])([A-Za-z0-9][A-Za-z0-9._-]*)\]"
)
_UNCLOSED_OPEN = re.compile(r"\[[A-Za-z0-9._-]+\s*$")
_SPACED_BRACKETS = re.compile(r"\[[^\[\]\n]* [^\[\]\n]*\]")
_EMPTY_BRACKETS = re.compile(r"\[\]")


def find_citations(answer_text: str) -> list[str]:
    """Extract [source-id] citations from generated text."""
    return _CITATION.findall(answer_text)


def find_malformed_citations(answer_text: str) -> list[str]:
    """Find citation-like fragments with broken syntax (ordered, deduped)."""
    spaced = list(_SPACED_BRACKETS.finditer(answer_text))
    spans = [(m.start(), m.end()) for m in spaced]
    found: list[str] = []
    for match in _DANGLING_CLOSE.finditer(answer_text):
        # A "word]" inside "[two words]" is reported once, as the
        # spaced fragment, not additionally as a dangling close.
        if not any(s <= match.start() and match.end() <= e for s, e in spans):
            found.append(match.group(0))
    unclosed = _UNCLOSED_OPEN.search(answer_text)
    if unclosed:
        found.append(unclosed.group(0).strip())
    found.extend(m.group(0) for m in spaced)
    found.extend(_EMPTY_BRACKETS.findall(answer_text))
    seen: set[str] = set()
    return [f for f in found if not (f in seen or seen.add(f))]


def validate_citations(answer_text: str, supplied_ids: list[str]) -> dict:
    """Check cited IDs against supplied IDs. Pure; never mutates text.

    Containment (every well-formed [id] was supplied) is NOT proof
    that claims are true or supported — only that the model cited
    given sources. `malformed` catches broken citation syntax, which
    containment alone cannot see. Claim-level semantic verification
    is beyond deterministic code; see docs/18.
    """
    found = find_citations(answer_text)
    supplied = set(supplied_ids)
    invalid = sorted({c for c in found if c not in supplied})
    malformed = find_malformed_citations(answer_text)
    return {
        "found": found,
        "supplied": list(supplied_ids),
        "contained": not invalid,
        "invalid": invalid,
        "malformed": malformed,
        "syntax_ok": not malformed,
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
    hygiene: dict | None = None,
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
        "hygiene": hygiene,
    }
