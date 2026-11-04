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
