"""Clarification handling for no-evidence questions (diagnostic milestone).

When retrieval finds nothing, a generic rejection is less useful than a
targeted clarification request. This module classifies the question with
transparent keyword rules over normalized tokens and returns a short
follow-up question. It NEVER answers the agricultural question, cites no
sources, and triggers no model call.

Rule lists are deliberately small and documented. They detect question
TOPICS (irrigation, rainfall, soil, crop choice, farmer-reported
problems), not dialects: nothing here claims to identify Moroccan
Darija.

HUMAN REVIEW PENDING: all Darija wording in MESSAGES and STILL_MISSING
below is approximate and must be reviewed and corrected by a Moroccan
Darija speaker before any production use. Wording lives only here so
review never touches application logic.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from localevoice.knowledge.retrieve import tokenize

GENERIC = "generic"
CROP_MANAGEMENT = "crop-management-context"
WEATHER_SEASONAL = "weather-seasonal-context"
LOCATION_DEPENDENT = "location-dependent-context"
SOIL_CONTEXT = "soil-context"
FARMER_DIAGNOSTIC = "farmer-diagnostic"

# Normalized-token triggers (see retrieve.tokenize: alef/ة/ى folding,
# ال-stripping, lowercasing). French forms included for code-switched
# questions. Order below defines priority on multiple matches.
_TRIGGERS: tuple[tuple[str, frozenset[str]], ...] = (
    (
        CROP_MANAGEMENT,
        frozenset(
            {"كتسقي", "تسقي", "يسقي", "سقي", "سقايه", "ماء", "irrigation",
             "arroser", "arrosage", "irriguer"}
        ),
    ),
    (
        WEATHER_SEASONAL,
        frozenset(
            {"تساقطات", "امطار", "مطر", "شتا", "طقس", "موسم", "مواسم",
             "pluie", "météo", "meteo", "saison"}
        ),
    ),
    (
        SOIL_CONTEXT,
        frozenset({"ارض", "اراضي", "تربه", "soil", "sol", "terres"}),
    ),
    (
        LOCATION_DEPENDENT,
        frozenset(
            {"احسن", "افضل", "مزروعات", "محاصيل", "زراعات", "منطقه",
             "جهه", "اقليم", "meilleur", "culture", "région"}
        ),
    ),
    (
        FARMER_DIAGNOSTIC,
        frozenset(
            {"مشاكل", "مشكل", "مشكله", "كتعاني", "تعاني", "يعاني",
             "معاناه", "problème", "probleme"}
        ),
    ),
)

MESSAGES: dict[str, str] = {
    CROP_MANAGEMENT: (
        "باش نعاونك فالسقي، خاصني نعرف شنو زارع. "
        "قوليا شنو هي المزروعات لي عندك؟"
    ),
    WEATHER_SEASONAL: (
        "التساقطات والموسم الفلاحي كيختلفو من منطقة لمنطقة. "
        "قوليا فأي إقليم ولا جماعة، و فأي موسم فلاحي؟"
    ),
    SOIL_CONTEXT: (
        "الحالة ديال الأرض كتحتاج معطيات محلية. "
        "واش عندك تحليل ديال التربة، ولا شنو لاحظتي فالأرض هاد العام؟"
    ),
    LOCATION_DEPENDENT: (
        "أحسن المزروعات كتعتمد على المنطقة والتربة والماء. "
        "فأي إقليم ولا جماعة الفلاحة ديالك؟"
    ),
    FARMER_DIAGNOSTIC: (
        "مرحبا. باش نعاونك، وصف ليا المشكل: شنو واقع بالضبط، "
        "فأي مزروعات، و من إيمتى بدا؟"
    ),
}

# Second-level abstention: used when context was collected but the corpus
# still has no evidence. Explains what remains unavailable; never answers.
STILL_MISSING: dict[str, str] = {
    CROP_MANAGEMENT: (
        "شكرا على التوضيح. حتى مع هاد المعطيات، ما لقيتش دليل على السقي "
        "فالمراجع المتوفرة، وما نبغيش نخمن. سول المستشار الفلاحي المحلي."
    ),
    WEATHER_SEASONAL: (
        "شكرا على التوضيح. ما عنديش معطيات التساقطات للمنطقة والموسم "
        "ديالك فالمراجع المتوفرة. سول المصالح الفلاحية المحلية."
    ),
    SOIL_CONTEXT: (
        "شكرا على التوضيح. ما عنديش دليل كافي على الحالة ديال الأرض. "
        "تحليل التربة عند مختبر محلي هو الخطوة اللازمة."
    ),
    LOCATION_DEPENDENT: (
        "شكرا على التوضيح. ما عنديش دليل على أحسن المزروعات لمنطقتك "
        "فالمراجع المتوفرة. سول المستشار الفلاحي المحلي."
    ),
    FARMER_DIAGNOSTIC: (
        "شكرا على التوضيح. ما لقيتش دليل مطابق فالمراجع، وما نبغيش "
        "نخمن. وصف الأعراض لبيطري ولا تقني محلي."
    ),
}


@dataclass(frozen=True)
class Clarification:
    category: str
    message: str | None  # None => use the generic insufficient message


def classify_question(question: str) -> Clarification:
    """Classify a no-evidence question; return its clarification, if any."""
    tokens = set(tokenize(question))
    for category, triggers in _TRIGGERS:
        if tokens & triggers:
            return Clarification(category=category, message=MESSAGES[category])
    return Clarification(category=GENERIC, message=None)


# Context slots: what a farmer response supplies. Normalized tokens (see
# retrieve.tokenize). Used to record which missing context arrived and to
# avoid asking twice for supplied information.
SLOT_TRIGGERS: tuple[tuple[str, frozenset[str]], ...] = (
    (
        "location",
        frozenset(
            {"اقليم", "جماعه", "منطقه", "جهه", "مدينه", "دوار", "قريه",
             "province", "commune", "region", "région", "ville", "village"}
        ),
    ),
    (
        "crop",
        frozenset(
            {"قمح", "زيتون", "مزروعات", "محاصيل", "زرع", "ذره", "شعير",
             "خضره", "طماطم", "بطاطس", "فواكه", "خضر", "لوبياء",
             "wheat", "olive", "olives", "maize", "barley", "blé",
             "cowpea", "niébé", "alfalfa", "luzerne", "برسيم"}
        ),
    ),
    (
        "animal",
        frozenset(
            {"بقر", "بقره", "غنم", "غنمه", "دجاج", "دجاجه", "ماعز",
             "معزه", "خروف", "خرفان", "عجل", "عجول", "جمل", "حصان",
             "ارنب", "cattle", "cow", "cows", "sheep", "goat", "goats",
             "chicken", "poultry", "livestock", "vache", "mouton",
             "chèvre", "chevre", "poulet", "bétail", "betail"}
        ),
    ),
    (
        "season",
        frozenset(
            {"موسم", "مواسم", "ربيع", "صيف", "شتا", "شتاء", "خريف",
             "عام", "سنه", "season", "saison"}
        ),
    ),
    (
        "soil",
        frozenset(
            {"تربه", "ارض", "تحليل", "رمليه", "طينيه", "soil"}
        ),
    ),
    (
        "problem",
        frozenset(
            {"مشاكل", "مشكل", "دوده", "مرض", "افه", "اعراض", "symptome"}
        ),
    ),
)


def extract_context_slots(text: str) -> list[str]:
    """Detect which context slots a farmer response fills (in fixed order)."""
    tokens = set(tokenize(text))
    return [slot for slot, triggers in SLOT_TRIGGERS if tokens & triggers]


# Recognized-value confidence: keyword-trigger matching is NOT named-entity
# recognition. A value is only "recognized" when its tokens match a term in
# the curated corpus (title/keywords/crop_or_species); everything else is
# unclassified, never guessed.
RECOGNIZED_CONFIDENCE = "corpus-match"


def build_value_index(documents: Iterable[Mapping[str, object]]) -> dict[str, set[str]]:
    """Map normalized token -> set of doc ids whose curated terms contain it.

    Curated terms are the doc title, keywords and crop_or_species field.
    Accepts Document objects or plain mappings.
    """
    index: dict[str, set[str]] = {}
    for doc in documents:
        if isinstance(doc, Mapping):
            doc_id = str(doc.get("id", ""))
            fields = [
                str(doc.get("title", "")),
                str(doc.get("crop_or_species", "")),
                " ".join(str(k) for k in (doc.get("keywords", []) or [])),
            ]
        else:  # Document
            doc_id = doc.id
            fields = [doc.title, doc.crop_or_species, " ".join(doc.keywords)]
        if not doc_id:
            continue
        for token in tokenize(" ".join(fields)):
            index.setdefault(token, set()).add(doc_id)
    return index


@dataclass(frozen=True)
class SlotValue:
    """A user-supplied value backed by a corpus term.

    value: the user's original wording (whitespace-separated word as typed).
    slot: the context slot the value belongs to ("crop" for corpus terms).
    confidence: always RECOGNIZED_CONFIDENCE; unrecognized words are
        reported via the unclassified list instead, never guessed.
    matched_docs: sorted doc ids whose curated terms contain the value.
    """

    value: str
    slot: str
    confidence: str
    matched_docs: tuple[str, ...]


@dataclass(frozen=True)
class SlotExtraction:
    values: tuple[SlotValue, ...]
    unclassified: tuple[str, ...]  # normalized tokens, neither slot nor value


def extract_slot_values(
    text: str, value_index: Mapping[str, set[str]]
) -> SlotExtraction:
    """Split a farmer response into recognized values and unclassified terms.

    A whitespace-separated word becomes a recognized value only when every
    one of its normalized tokens maps to the SAME document id(s) in the
    value index. Trigger words that merely name a slot (e.g. "منطقة") stay
    out of values; proper nouns absent from the corpus (e.g. "سوس ماسة")
    land in unclassified with no guessed identity.
    """
    slot_tokens = {tok for _, triggers in SLOT_TRIGGERS for tok in triggers}
    values: list[SlotValue] = []
    unclassified: list[str] = []
    for word in text.split():
        tokens = tokenize(word)
        if not tokens:
            continue
        doc_sets = [value_index.get(tok, set()) for tok in tokens]
        shared = set.intersection(*doc_sets) if doc_sets else set()
        if shared and all(doc_sets):
            values.append(
                SlotValue(
                    value=word,
                    slot="crop",
                    confidence=RECOGNIZED_CONFIDENCE,
                    matched_docs=tuple(sorted(shared)),
                )
            )
        else:
            for tok in tokens:
                if tok not in slot_tokens and tok not in value_index:
                    unclassified.append(tok)
    # Deduplicate unclassified, preserving first-seen order.
    seen: set[str] = set()
    unique = [t for t in unclassified if not (t in seen or seen.add(t))]
    return SlotExtraction(values=tuple(values), unclassified=tuple(unique))
