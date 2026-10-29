"""Question-answering pipeline: retrieve, then generate a grounded answer."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from localevoice.knowledge.corpus import Corpus, CorpusError
from localevoice.knowledge.retrieve import Evidence, retrieve
from localevoice.providers.meta_chat import (
    ConfigurationError,
    MetaChatError,
    chat_complete,
    resolve_model,
)

SYSTEM_PROMPT = """You answer farming questions for a Moroccan farmer. Rules:
1. Use ONLY the evidence passages below as the factual basis for agricultural claims. Each passage is labeled with its source ID.
2. If the evidence does not answer the question, say so plainly and do not guess. Never invent facts, citations, or source IDs.
3. Cite every agricultural claim with the source ID in square brackets, e.g. [feedipedia-wheat-grain]. Never cite a source ID that was not supplied to you.
4. Prefer concise, understandable Moroccan Darija when the question is in Darija or Arabic script; otherwise match the question's language simply.
5. Distinguish general information from advice that needs a local agronomist or veterinarian. Ask for missing context (crop, animal, location, season, symptoms) when it materially affects the recommendation.
6. Do not give chemical, pesticide, dosage, or treatment instructions unless they appear verbatim in the supplied evidence; if absent, say a qualified local specialist must decide.
7. Keep uncertainty visible: say what is unknown."""

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I could not find relevant evidence for this question in the available "
    "reference material, so I will not guess an answer. Try rephrasing with "
    "the crop or animal name (for example: wheat/القمح/blé, olive cake, "
    "cowpea), or ask your local agricultural advisor."
)

_ARABIC_CHAR = re.compile(r"[\u0600-\u06ff]")
_CITATION = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9._-]*)\]")


@dataclass
class LanguageInfo:
    requested: str | None
    inferred: str
    uncertain: bool


@dataclass
class AnswerResult:
    question: str
    answer_text: str
    language: LanguageInfo
    source_ids_supplied: list[str]
    evidence: list[dict]
    insufficient_evidence: bool
    model: str | None
    elapsed_ms: int | None
    error: dict | None = None

    def to_run_record(self) -> dict:
        """Serialize for saving. Never contains API keys."""
        record = asdict(self)
        record["language"] = asdict(self.language)
        return record


def infer_language(question: str, requested: str | None = None) -> LanguageInfo:
    """Infer script/language with explicit uncertainty.

    Heuristic only: Arabic script present -> Darija/Arabic assumed uncertain;
    otherwise the question language is unknown. Never claims validated
    dialect identification.
    """
    if requested:
        return LanguageInfo(
            requested=requested, inferred=requested, uncertain=False
        )
    if _ARABIC_CHAR.search(question):
        return LanguageInfo(
            requested=None,
            inferred="darija-or-arabic (arabic-script, uncertain)",
            uncertain=True,
        )
    return LanguageInfo(
        requested=None, inferred="unknown (latin-script, uncertain)", uncertain=True
    )


def find_citations(answer_text: str) -> list[str]:
    """Extract [source-id] citations from generated text."""
    return _CITATION.findall(answer_text)


def build_messages(
    question: str, evidence: list[Evidence], language: LanguageInfo
) -> list[dict[str, str]]:
    """Build the grounded-generation prompt. Evidence is the only source."""
    parts = [
        f"Question ({language.inferred}): {question}",
        "",
        "Evidence passages (the ONLY permitted factual basis):",
    ]
    for item in evidence:
        parts.append(
            f"--- source [{item.document_id}] ({item.title}, {item.publisher}) ---\n"
            f"{item.content}"
        )
    parts.append("")
    parts.append(
        "Answer the question using only the evidence above, "
        "following all rules in the system prompt."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(parts)},
    ]


def answer_question(
    question: str,
    corpus: Corpus,
    *,
    top_k: int = 3,
    min_score: int = 1,
    language: str | None = None,
    chat_fn: Callable[..., str] = chat_complete,
    timeout: float = 90.0,
) -> AnswerResult:
    """Retrieve evidence and generate a grounded answer.

    No relevant evidence -> transparent insufficient-evidence response with
    no model call. Meta API failures -> result with error detail, no
    fabricated answer. `chat_fn` is injectable so unit tests avoid the
    network.
    """
    if not question or not question.strip():
        raise ValueError("question must be a non-empty string")
    if not corpus.documents:
        raise CorpusError("Corpus is empty: no documents to search.")

    lang = infer_language(question, language)
    found = retrieve(question, corpus.documents, top_k=top_k)
    relevant = [e for e in found if e.score >= min_score]

    evidence_dicts = [
        {
            "document_id": e.document_id,
            "title": e.title,
            "publisher": e.publisher,
            "source_url": e.source_url,
            "score": e.score,
            "matched_terms": list(e.matched_terms),
        }
        for e in relevant
    ]

    if not relevant:
        return AnswerResult(
            question=question,
            answer_text=INSUFFICIENT_EVIDENCE_MESSAGE,
            language=lang,
            source_ids_supplied=[],
            evidence=[],
            insufficient_evidence=True,
            model=None,
            elapsed_ms=None,
        )

    messages = build_messages(question, relevant, lang)
    try:
        model_id = resolve_model()
    except ConfigurationError as exc:
        return AnswerResult(
            question=question,
            answer_text="Answer generation is unavailable: "
            f"{exc} No answer was generated.",
            language=lang,
            source_ids_supplied=[e.document_id for e in relevant],
            evidence=evidence_dicts,
            insufficient_evidence=False,
            model=None,
            elapsed_ms=None,
            error={"type": "ConfigurationError", "message": str(exc)},
        )

    start = time.monotonic()
    try:
        answer_text = chat_fn(messages, timeout=timeout)
    except (ConfigurationError, MetaChatError) as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        return AnswerResult(
            question=question,
            answer_text="Answer generation failed and no answer is available. "
            f"Detail: {exc}",
            language=lang,
            source_ids_supplied=[e.document_id for e in relevant],
            evidence=evidence_dicts,
            insufficient_evidence=False,
            model=model_id,
            elapsed_ms=elapsed,
            error={"type": type(exc).__name__, "message": str(exc)},
        )
    elapsed = int((time.monotonic() - start) * 1000)
    return AnswerResult(
        question=question,
        answer_text=answer_text,
        language=lang,
        source_ids_supplied=[e.document_id for e in relevant],
        evidence=evidence_dicts,
        insufficient_evidence=False,
        model=model_id,
        elapsed_ms=elapsed,
    )
