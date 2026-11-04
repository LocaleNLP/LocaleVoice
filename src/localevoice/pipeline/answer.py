"""Question-answering pipeline: retrieve, then generate a grounded answer."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from localevoice.knowledge.corpus import Corpus, CorpusError, is_answer_eligible
from localevoice.knowledge.retrieve import (
    Evidence,
    normalize_for_search,
    retrieve,
    score_document,
    tokenize,
)
from localevoice.pipeline.clarify import GENERIC, classify_question
from localevoice.pipeline.intent import UNSUPPORTED_GENERAL, classify_intent
from localevoice.pipeline.trace import (
    build_trace,
    find_citations,
    validate_citations,
)
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
7. Keep uncertainty visible: say what is unknown.
8. Never invent, rename, or cite a Feedipedia source or document ID. Only the source IDs listed above exist; if none of them supports a claim, say the evidence does not cover it."""

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I could not find relevant evidence for this question in the available "
    "reference material, so I will not guess an answer. Try rephrasing with "
    "the crop or animal name (for example: wheat/القمح/blé, olive cake, "
    "cowpea), or ask your local agricultural advisor."
)

_ARABIC_CHAR = re.compile(r"[\u0600-\u06ff]")


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
    clarification_category: str | None = None
    intent: str | None = None
    trace: dict | None = None

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
    intent_info = classify_intent(question)
    query_tokens = tokenize(question)
    found = retrieve(question, corpus.documents, top_k=top_k)
    eligible = {d.id for d in corpus.documents if is_answer_eligible(d)}
    relevant = [
        e for e in found if e.score >= min_score and e.document_id in eligible
    ]
    selected_ids = [e.document_id for e in relevant]
    found_ids = {e.document_id for e in found}

    considered: dict[str, dict] = {}
    for doc in corpus.documents:
        doc_score, matched = score_document(query_tokens, doc)
        if doc.id in selected_ids:
            reason = "selected"
        elif doc_score > 0 and doc.id not in eligible:
            reason = (
                f"excluded: review_status={doc.review_status} "
                "(not farmer-facing eligible)"
            )
        elif doc_score <= 0:
            reason = "no matched terms"
        elif doc.id in found_ids:
            reason = f"score {doc_score} below min_score {min_score}"
        else:
            reason = f"rank beyond top_k {top_k}"
        considered[doc.id] = {
            "score": doc_score,
            "matched": matched,
            "selected": doc.id in selected_ids,
            "reason": reason,
        }

    def _trace(
        *,
        sufficient: bool,
        clarification_requested: bool,
        model_called: bool,
        model_id: str | None,
        citation_check: dict | None,
        status: str,
        category: str | None,
        error_type: str | None = None,
    ) -> dict:
        return build_trace(
            question=question,
            normalized_question=normalize_for_search(question),
            intent=intent_info.name,
            category=category,
            keywords=query_tokens,
            considered=considered,
            selected_ids=selected_ids,
            min_score=min_score,
            top_k=top_k,
            sufficient=sufficient,
            clarification_requested=clarification_requested,
            model_called=model_called,
            model_id=model_id,
            citation_check=citation_check,
            status=status,
            error_type=error_type,
        )

    if intent_info.response is not None:
        # Social or out-of-domain intent: instant canned response, never
        # a model call. Retrieval still ran above so the trace is complete.
        unsupported = intent_info.name == UNSUPPORTED_GENERAL
        return AnswerResult(
            question=question,
            answer_text=intent_info.response,
            language=lang,
            source_ids_supplied=[],
            evidence=[],
            insufficient_evidence=unsupported,
            model=None,
            elapsed_ms=None,
            clarification_category=GENERIC if unsupported else None,
            intent=intent_info.name,
            trace=_trace(
                sufficient=False,
                clarification_requested=False,
                model_called=False,
                model_id=None,
                citation_check=None,
                status=f"intent:{intent_info.name}",
                category=None,
            ),
        )

    evidence_dicts = [
        {
            "document_id": e.document_id,
            "title": e.title,
            "publisher": e.publisher,
            "source_url": e.source_url,
            "score": e.score,
            "matched_terms": list(e.matched_terms),
            "category": e.category,
        }
        for e in relevant
    ]

    if not relevant:
        clarification = classify_question(question)
        return AnswerResult(
            question=question,
            answer_text=clarification.message or INSUFFICIENT_EVIDENCE_MESSAGE,
            clarification_category=clarification.category,
            intent=intent_info.name,
            language=lang,
            source_ids_supplied=[],
            evidence=[],
            insufficient_evidence=True,
            model=None,
            elapsed_ms=None,
            trace=_trace(
                sufficient=False,
                clarification_requested=clarification.category != GENERIC,
                model_called=False,
                model_id=None,
                citation_check=None,
                status="insufficient",
                category=None,
            ),
        )

    top_category = relevant[0].category or None
    messages = build_messages(question, relevant, lang)
    try:
        model_id = resolve_model()
    except ConfigurationError as exc:
        return AnswerResult(
            question=question,
            answer_text="Answer generation is unavailable: "
            f"{exc} No answer was generated.",
            language=lang,
            source_ids_supplied=selected_ids,
            evidence=evidence_dicts,
            insufficient_evidence=False,
            model=None,
            elapsed_ms=None,
            error={"type": "ConfigurationError", "message": str(exc)},
            intent=intent_info.name,
            trace=_trace(
                sufficient=True,
                clarification_requested=False,
                model_called=False,
                model_id=None,
                citation_check=None,
                status="error",
                category=top_category,
                error_type="ConfigurationError",
            ),
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
            source_ids_supplied=selected_ids,
            evidence=evidence_dicts,
            insufficient_evidence=False,
            model=model_id,
            elapsed_ms=elapsed,
            error={"type": type(exc).__name__, "message": str(exc)},
            intent=intent_info.name,
            trace=_trace(
                sufficient=True,
                clarification_requested=False,
                model_called=True,
                model_id=model_id,
                citation_check=None,
                status="error",
                category=top_category,
                error_type=type(exc).__name__,
            ),
        )
    elapsed = int((time.monotonic() - start) * 1000)
    citation_check = validate_citations(answer_text, selected_ids)
    return AnswerResult(
        question=question,
        answer_text=answer_text,
        intent=intent_info.name,
        language=lang,
        source_ids_supplied=selected_ids,
        evidence=evidence_dicts,
        insufficient_evidence=False,
        model=model_id,
        elapsed_ms=elapsed,
        trace=_trace(
            sufficient=True,
            clarification_requested=False,
            model_called=True,
            model_id=model_id,
            citation_check=citation_check,
            status="answered",
            category=top_category,
        ),
    )
