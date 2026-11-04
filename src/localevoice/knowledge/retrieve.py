"""Deterministic lexical retrieval baseline (Milestone 2).

Search-only normalization; the original query text is never modified.
This baseline matches shared vocabulary (including French and Arabic-script
terms present in the corpus). It does not understand Darija semantics, and
must not be described as doing so.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

from localevoice.knowledge.corpus import Document, is_answer_eligible

# Documented search-only normalization for Arabic script (conservative):
# - NFKC compatibility fold, strip Arabic diacritics (tashkeel) and tatweel.
# - Alef variants (أ إ آ) -> ا; ta marbuta ة -> ه; alef maqsura ى -> ي.
# - Hamza-on-waw (ؤ) -> و; hamza-on-ya (ئ) -> ي (spelling variation).
# Latin text is lowercased. Punctuation is replaced with spaces. As light
# stemming, the Arabic definite article prefix ال is stripped from tokens
# longer than 4 characters (so القمح matches قمح). Single-character tokens
# and STOPWORDS are dropped. All search-only; stored text and the user's
# query string are never altered.
_AR_DIACRITICS = re.compile(r"[\u064b-\u0652\u0670]")
_AR_PUNCT = re.compile(r"[؟،؛]")
_AR_NORM = str.maketrans(
    {"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "ـ": "", "ؤ": "و", "ئ": "ي"}
)
_NON_TOKEN = re.compile(r"[^\w\u0600-\u06ff]+", re.UNICODE)

# Baseline precision guard: high-frequency function words carry no topical
# signal for lexical matching, so they are dropped from BOTH query and
# document tokens before scoring. Without this, any English question matches
# every English document via "is/the/of". This is a fixed minimal list, not
# a linguistic claim about Darija stopwords.
STOPWORDS = frozenset(
    """
    a an and are as at be but by for from has have in is it of on or that the
    this to was what when with you your much many more most
    le la les de des du un une des et ou est sont il ils elle elles pour
    dans avec pas plus tout toute
    واش شنو شنهو هي هو هوما ديال في من علي على الى الي هل ما لا نعم هاد هدي
    هدا كان كانت كاين كاينة غير بلا حتى اما او ام
    """.split()
)


def normalize_for_search(text: str) -> str:
    """Normalize text for lexical matching. Search use only."""
    folded = unicodedata.normalize("NFKC", text)
    folded = _AR_PUNCT.sub(" ", folded)
    folded = _AR_DIACRITICS.sub("", folded)
    folded = folded.translate(_AR_NORM)
    folded = folded.lower()
    folded = _NON_TOKEN.sub(" ", folded)
    return re.sub(r"\s+", " ", folded).strip()


def _strip_prefixes(token: str) -> str:
    """Strip fused preposition+article prefixes, then a bare ال article.

    Only strips ف/ب/ل when fused with the article (فال/بال/لل + stem),
    e.g. فالطماطم -> طماطم, للغنم -> غنم, للبقر -> بقر. Genuine
    ف/ب-initial words (برسيم, فواكه, فلاحه, بصله) are preserved, as
    are short roots (فول, بقر, لحم: remainder must be 3+ chars).
    The و- conjunction is deliberately NOT stripped; و-prefixed
    words stay unrecognized (documented limitation).
    """
    if len(token) >= 6 and token[0] in "فب" and token[1:3] == "ال":
        token = token[3:]  # فالطماطم -> طماطم
    elif len(token) >= 5 and token.startswith("لل"):
        token = token[2:]  # للغنم -> غنم (article alef elided in writing)
    if len(token) > 4 and token.startswith("ال"):
        stemmed = token[2:]
        if len(stemmed) >= 3:
            token = stemmed
    return token


def tokenize(text: str) -> list[str]:
    """Split normalized text into search tokens (search-only stemming)."""
    normalized = normalize_for_search(text)
    if not normalized:
        return []
    tokens = []
    for raw in normalized.split():
        raw = _strip_prefixes(raw)
        if len(raw) < 2:  # drop single-character noise (e.g. "d" from "d'olive")
            continue
        if raw in STOPWORDS:
            continue
        tokens.append(raw)
    return tokens


@dataclass(frozen=True)
class Evidence:
    """Retrieval view over a Document. Field names are the stable internal
    contract (prompt citations, UI, eval); values map from the 4D
    Document schema (id/source_name/excerpt/keywords)."""

    document_id: str
    title: str
    publisher: str
    source_url: str
    content: str
    score: float
    matched_terms: tuple[str, ...]
    category: str = ""


def _doc_tokens(doc: Document) -> set[str]:
    tokens = set(tokenize(doc.excerpt))
    for alias in doc.keywords:
        tokens.update(tokenize(alias))
    tokens.update(tokenize(doc.title))
    return tokens


def score_document(query_tokens: list[str], doc: Document) -> tuple[int, list[str]]:
    """Score a document: number of distinct query tokens matched.

    Returns (score, matched_terms). Deterministic; ties broken by callers
    on document_id. This count scoring is the reproducible baseline.
    """
    if not query_tokens:
        return 0, []
    available = _doc_tokens(doc)
    matched = sorted({t for t in query_tokens if t in available})
    return len(matched), matched


def _idf_weights(
    query_tokens: list[str], doc_token_sets: list[set[str]]
) -> dict[str, float]:
    """IDF weight per matched query token: log((1+N)/(1+df)) + 1."""
    total = len(doc_token_sets)
    weights = {}
    for token in set(query_tokens):
        df = sum(1 for s in doc_token_sets if token in s)
        weights[token] = math.log((1 + total) / (1 + df)) + 1
    return weights


def retrieve(
    query: str,
    documents: list[Document],
    top_k: int = 3,
    weighting: str = "count",
    eligible_only: bool = False,
) -> list[Evidence]:
    """Rank documents against the query; return at most top_k with score > 0.

    Empty or whitespace-only queries return []. The query string itself is
    never altered.

    Thresholds (explicit, configurable by callers): top_k caps returned
    evidence; callers apply min_score afterwards (see answer_question).
    weighting="count" (default) is the reproducible baseline: score is
    the matched-term count. weighting="idf" sorts by IDF-weighted sum
    so distinctive agricultural terms outrank ubiquitous ones; score is
    then a rounded weighted sum rather than a count.

    eligible_only=True restricts ranking to verified excerpts
    (review-status enforcement, Milestones 5.1/6B): pending-review,
    rejected, and archived documents cannot occupy rank slots. All
    farmer-facing and evaluation consumers must pass True; the
    default False preserves the raw ranking for diagnostics.
    """
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    if weighting not in ("count", "idf"):
        raise ValueError("weighting must be 'count' or 'idf'")
    if eligible_only:
        documents = [d for d in documents if is_answer_eligible(d)]
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    doc_token_sets = [_doc_tokens(doc) for doc in documents]
    idf = _idf_weights(query_tokens, doc_token_sets) if weighting == "idf" else {}
    scored: list[Evidence] = []
    for doc, available in zip(documents, doc_token_sets):
        matched = sorted({t for t in query_tokens if t in available})
        if not matched:
            continue
        if weighting == "idf":
            score = round(sum(idf[t] for t in matched), 4)
        else:
            score = len(matched)
        scored.append(
            Evidence(
                document_id=doc.id,
                title=doc.title,
                publisher=doc.source_name,
                source_url=doc.source_url,
                content=doc.excerpt,
                score=score,
                matched_terms=tuple(matched),
                category=doc.category,
            )
        )
    scored.sort(key=lambda e: (-e.score, e.document_id))
    return scored[:top_k]
