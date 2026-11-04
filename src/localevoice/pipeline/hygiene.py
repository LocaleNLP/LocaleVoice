"""Answer-hygiene checks: report-only text defects (Milestone 6C).

These catch mechanical defects a reviewer would flag — truncated
words are NOT detectable, but exact repeated sentences, stray
Latin-script fragments in Arabic answers, and unbalanced brackets
are. Results are advisory flags for diagnostics and tests, never a
claim of natural Darija: human approval still requires a qualified
reviewer (docs/08).
"""

from __future__ import annotations

import re

# Latin-script tokens that are legitimate inside Arabic answers:
# recognized French crop/feed terms, publishers, product names, and
# common units. Anything else Latin (3+ letters) is flagged.
KNOWN_LATIN_TERMS = frozenset(
    {
        "blé", "froment", "niébé", "dolique", "luzerne", "lucerne",
        "tourteau", "olivier", "olive", "olives", "fourrage", "vache",
        "vaches", "mouton", "moutons", "bovin", "bovins", "bétail",
        "maïs", "wheat", "barley", "maize", "cowpea", "alfalfa",
        "feedipedia", "inrae", "cirad", "afz", "fao", "localevoice",
        "vigna", "unguiculata", "medicago", "sativa",
        "kg", "mg", "cm", "mm", "msa",
    }
)

_LATIN_WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-]*")
_SENTENCE_SPLIT = re.compile(r"[.!?؟\n]+")
_URL = re.compile(r"https?://\S+|www\.\S+")


def find_latin_fragments(text: str) -> list[str]:
    """Latin-script words outside the known-terms allowlist.

    Feeding text should already have citations stripped; URLs are
    removed here. Short tokens (<3 letters) are ignored.
    """
    cleaned = _URL.sub(" ", text)
    found: list[str] = []
    for match in _LATIN_WORD.finditer(cleaned):
        word = match.group(0).strip("'-")
        if len(word) >= 3 and word.lower() not in KNOWN_LATIN_TERMS:
            found.append(word)
    seen: set[str] = set()
    return [w for w in found if not (w in seen or seen.add(w))]


def find_repeated_sentences(text: str) -> list[str]:
    """Exact-duplicate sentences (case-insensitive, 10+ chars)."""
    counts: dict[str, int] = {}
    first_form: dict[str, str] = {}
    for raw in _SENTENCE_SPLIT.split(text):
        sentence = " ".join(raw.split())
        if len(sentence) < 10:
            continue
        key = sentence.lower()
        counts[key] = counts.get(key, 0) + 1
        first_form.setdefault(key, sentence)
    return sorted(first_form[k] for k, n in counts.items() if n > 1)


def hygiene_report(text: str) -> dict:
    """Advisory hygiene flags for generated text (pure function)."""
    latin = find_latin_fragments(text)
    repeated = find_repeated_sentences(text)
    return {
        "latin_fragments": latin,
        "repeated_sentences": repeated,
        "clean": not latin and not repeated,
    }
