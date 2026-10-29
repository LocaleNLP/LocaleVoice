"""Reproducible offline/live evaluation over versioned fixtures."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from localevoice.knowledge.corpus import Corpus
from localevoice.knowledge.retrieve import retrieve
from localevoice.pipeline.answer import (
    answer_question,
    find_citations,
)


@dataclass
class Fixture:
    id: str
    question: str
    language_label: str
    relevant_doc_ids: list[str]
    expect_insufficient: bool
    category: str
    human_review: dict | None = None


@dataclass
class ItemReport:
    id: str
    category: str
    retrieved_ids: list[str]
    retrieval_scores: dict[str, int]
    relevant_recalled: bool
    insufficient_triggered: bool
    insufficient_expected: bool
    insufficient_correct: bool
    citations: list[str] = field(default_factory=list)
    citations_within_supplied: bool | None = None
    model: str | None = None
    elapsed_ms: int | None = None
    error: dict | None = None
    human_review: dict | None = None


def load_fixtures(path: str) -> tuple[dict, list[Fixture]]:
    """Load evaluation fixtures; return (metadata, items)."""
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict) or not isinstance(
        payload.get("items"), list
    ):
        raise ValueError("fixtures file must be an object with an items list")
    items = []
    for raw in payload["items"]:
        for name in (
            "id",
            "question",
            "language_label",
            "relevant_doc_ids",
            "expect_insufficient",
            "category",
        ):
            if name not in raw:
                raise ValueError(f"fixture missing field: {name}")
        items.append(
            Fixture(
                id=raw["id"],
                question=raw["question"],
                language_label=raw["language_label"],
                relevant_doc_ids=list(raw["relevant_doc_ids"]),
                expect_insufficient=bool(raw["expect_insufficient"]),
                category=raw["category"],
                human_review=raw.get("human_review"),
            )
        )
    metadata = {k: v for k, v in payload.items() if k != "items"}
    return metadata, items


def evaluate_item(
    fixture: Fixture,
    corpus: Corpus,
    *,
    top_k: int = 3,
    min_score: int = 1,
    live: bool = False,
    chat_fn: Callable[..., str] | None = None,
) -> ItemReport:
    """Evaluate one fixture. Offline by default (no model calls).

    Offline mode checks retrieval recall and the insufficient-evidence gate.
    Live mode additionally generates an answer and checks that citations
    stay within supplied source IDs.
    """
    found = retrieve(fixture.question, corpus.documents, top_k=top_k)
    relevant = [e for e in found if e.score >= min_score]
    retrieved_ids = [e.document_id for e in relevant]
    insufficient = not relevant
    expected_relevant = set(fixture.relevant_doc_ids)
    recalled = bool(expected_relevant) and bool(
        expected_relevant & set(retrieved_ids)
    )
    if not expected_relevant:
        recalled = not retrieved_ids

    report = ItemReport(
        id=fixture.id,
        category=fixture.category,
        retrieved_ids=retrieved_ids,
        retrieval_scores={e.document_id: e.score for e in relevant},
        relevant_recalled=recalled,
        insufficient_triggered=insufficient,
        insufficient_expected=fixture.expect_insufficient,
        insufficient_correct=insufficient == fixture.expect_insufficient,
        human_review=fixture.human_review,
    )

    if live:
        if chat_fn is None:
            from localevoice.providers.meta_chat import chat_complete

            chat_fn = chat_complete
        result = answer_question(
            fixture.question,
            corpus,
            top_k=top_k,
            min_score=min_score,
            chat_fn=chat_fn,
        )
        citations = find_citations(result.answer_text)
        supplied = set(result.source_ids_supplied)
        report.citations = citations
        report.citations_within_supplied = all(c in supplied for c in citations)
        report.model = result.model
        report.elapsed_ms = result.elapsed_ms
        report.error = result.error
    return report


def evaluate_all(
    fixtures: list[Fixture],
    corpus: Corpus,
    *,
    top_k: int = 3,
    min_score: int = 1,
    live: bool = False,
    chat_fn: Callable[..., str] | None = None,
) -> list[ItemReport]:
    return [
        evaluate_item(
            fx, corpus, top_k=top_k, min_score=min_score, live=live, chat_fn=chat_fn
        )
        for fx in fixtures
    ]


def summarize(reports: list[ItemReport]) -> dict:
    total = len(reports)
    return {
        "total": total,
        "relevant_recalled": sum(1 for r in reports if r.relevant_recalled),
        "insufficient_correct": sum(1 for r in reports if r.insufficient_correct),
        "citation_checks": sum(
            1 for r in reports if r.citations_within_supplied is not None
        ),
        "citations_within_supplied": sum(
            1 for r in reports if r.citations_within_supplied
        ),
        "errors": sum(1 for r in reports if r.error),
    }


def write_report(path: str, metadata: dict, reports: list[ItemReport]) -> None:
    """Write a JSON evaluation report. Contains no API keys."""
    payload = {
        "metadata": metadata,
        "summary": summarize(reports),
        "items": [asdict(r) for r in reports],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
