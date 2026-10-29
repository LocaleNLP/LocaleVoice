"""Deterministic lexical retrieval baseline (Milestone 2).

Search-only normalization; the original query text is never modified.
This baseline matches shared vocabulary (including French and Arabic-script
terms present in the corpus). It does not understand Darija semantics, and
must not be described as doing so.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from localevoice.knowledge.corpus import Document

# Documented search-only normalization for Arabic script (conservative):
# - NFKC compatibility fold, strip Arabic diacritics (tashkeel) and tatweel.
# - Alef variants (أ إ آ) -> ا; ta marbuta ة -> ه; alef maqsura ى -> ي.
# Latin text is lowercased. Punctuation is replaced with spaces. As light
# stemming, the Arabic definite article prefix ال is stripped from tokens
# longer than 4 characters (so القمح matches قمح). This is search-only and
# does not alter stored text or the user's query string.
_AR_DIACRITICS = re.compile(r"[\u064b-\u0652\u0670]")
_AR_NORM = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "ـ": ""})
_NON_TOKEN = re.compile(r"[^\w\u0600-\u06ff]+", re.UNICODE)


def normalize_for_search(text: str) -> str:
    """Normalize text for lexical matching. Search use only."""
    folded = unicodedata.normalize("NFKC", text)
    folded = _AR_DIACRITICS.sub("", folded)
    folded = folded.translate(_AR_NORM)
    folded = folded.lower()
    folded = _NON_TOKEN.sub(" ", folded)
    return re.sub(r"\s+", " ", folded).strip()


def tokenize(text: str) -> list[str]:
    """Split normalized text into search tokens (search-only stemming)."""
    normalized = normalize_for_search(text)
    if not normalized:
        return []
    tokens = []
    for raw in normalized.split():
        if len(raw) > 4 and raw.startswith("ال"):
            raw = raw[2:]
        if len(raw) < 2:  # drop single-character noise (e.g. "d" from "d'olive")
            continue
        tokens.append(raw)
    return tokens


@dataclass(frozen=True)
class Evidence:
    document_id: str
    title: str
    publisher: str
    source_url: str
    content: str
    score: int
    matched_terms: tuple[str, ...]


def _doc_tokens(doc: Document) -> set[str]:
    tokens = set(tokenize(doc.content))
    for alias in doc.search_aliases:
        tokens.update(tokenize(alias))
    tokens.update(tokenize(doc.title))
    return tokens


def score_document(query_tokens: list[str], doc: Document) -> tuple[int, list[str]]:
    """Score a document: number of distinct query tokens matched.

    Returns (score, matched_terms). Deterministic; ties broken by callers
    on document_id.
    """
    if not query_tokens:
        return 0, []
    available = _doc_tokens(doc)
    matched = sorted({t for t in query_tokens if t in available})
    return len(matched), matched


def retrieve(
    query: str, documents: list[Document], top_k: int = 3
) -> list[Evidence]:
    """Rank documents against the query; return at most top_k with score > 0.

    Empty or whitespace-only queries return []. The query string itself is
    never altered.
    """
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    scored: list[Evidence] = []
    for doc in documents:
        score, matched = score_document(query_tokens, doc)
        if score > 0:
            scored.append(
                Evidence(
                    document_id=doc.document_id,
                    title=doc.title,
                    publisher=doc.publisher,
                    source_url=doc.source_url,
                    content=doc.content,
                    score=score,
                    matched_terms=tuple(matched),
                )
            )
    scored.sort(key=lambda e: (-e.score, e.document_id))
    return scored[:top_k]
