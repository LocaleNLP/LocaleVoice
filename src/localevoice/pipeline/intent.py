"""Deterministic intent classification (Milestone 4D).

Rule-based layer consulted before retrieval. Social intents (greeting,
thanks, goodbye) resolve instantly with canned responses and NEVER call
the model; unsupported-domain questions abstain immediately with a
domain message; everything else flows to retrieval unchanged.

Design constraints (tested):
- A greeting matches ONLY when every token is a greeting token. Mixed
  messages ("hello, is wheat good?") fall through to retrieval.
- Arabic script alone never implies any intent.
- Ambiguous messages fall through to retrieval (unclear), never to a
  fabricated answer and never mislabeled as supported.

HUMAN REVIEW PENDING: all Darija wording in RESPONSES below is
approximate and must be reviewed by a Moroccan Darija speaker.
Wording lives only here so review never touches application logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from localevoice.knowledge.retrieve import tokenize

GREETING = "greeting"
THANKS = "thanks"
GOODBYE = "goodbye"
AGRICULTURAL_QUESTION = "agricultural_question"
UNSUPPORTED_GENERAL = "unsupported_general_question"
UNCLEAR = "unclear"

# Normalized tokens as produced by retrieve.tokenize (alef/ة/ى folding,
# ال-stripping, stopword removal). Trigger sets below use those folded
# forms, e.g. "السلام" arrives as "سلام".
_GREETING_TOKENS = frozenset(
    """
    سلام عليكم ورحمه له الله صباح خير مساء نور مرحبا بك بيك اهلا
    salam bonjour salut hello hi hey good morning afternoon
    """.split()
)

_THANKS_TOKENS = frozenset(
    {"شكرا", "شكر", "متشكر", "بارك", "له", "الله", "فيك", "بزاف",
     "جزيلا", "merci", "thanks", "thank"}
)
# Pure modifiers alone ("بزاف", "جزيلا") are not thanks; one head token
# must be present. بارك heads the "بارك الله فيك" thanks expression.
_THANKS_CORE = frozenset(
    {"شكرا", "شكر", "متشكر", "بارك", "merci", "thanks", "thank"}
)

_GOODBYE_TOKENS = frozenset(
    {"بسلامه", "سلامه", "وداعا", "مع", "au", "revoir", "bye", "goodbye"}
)

# Tiny explicit list of clearly non-agricultural topics. Anything not
# listed here is NOT unsupported-by-rule; it flows to retrieval.
_UNSUPPORTED_TRIGGERS = frozenset(
    {
        "عاصمه", "capital", "capitale",
        "رياضه", "sport", "football", "كره",
        "سياسه", "politique", "انتخابات",
        "دين", "religion", "سينما", "cinema", "موسيقي", "musique",
    }
)

# Agricultural signals: clarify topics + corpus/crop/livestock vocabulary.
# Presence suggests agricultural_question; absence means unclear (both flow
# to retrieval — the label only records the signal for the trace).
_AG_SIGNALS = frozenset(
    """
    قمح بل wheat كتسقي تسقي يسقي سقي ماء irrigation arroser arrosage
    تساقطات امطار مطر شتا طقس موسم مواسم pluie saison
    ارض اراضي تربه soil sol terres
    احسن افضل مزروعات محاصيل زراعات منطقه جهه اقليم زرع فلاحه فلاحي
    مشاكل مشكل كتعاني تعاني علف بقره بقر غنم ماعز دجاج حيوان
    cowpea olive blé froment niébé olivier زيتون لوبياء tourteau
    alfalfa luzerne lucerne fourrage vache vaches mouton moutons
    feed ruminant cattle cows sheep goat goats dairy bovin bovins
    crop crops harvest سماد دواء مرض
    """.split()
)

RESPONSES: dict[str, str] = {
    GREETING: (
        "وعليكم السلام! مرحبا بك في LocaleVoice. "
        "كيف نقدر نعاونك اليوم فالفلاحة؟"
    ),
    THANKS: "العفو! إلا كان عندك شي سؤال آخر على الفلاحة، مرحبا.",
    GOODBYE: "بسلامة! الله يعاونك فالفلاحة ديالك.",
    UNSUPPORTED_GENERAL: (
        "LocaleVoice حاليا كيجاوب غير على الأسئلة الفلاحة. "
        "صيفط ليا سؤال على المزروعات، التربة، السقي، ولا تربية المواشي."
    ),
}


@dataclass(frozen=True)
class Intent:
    name: str
    response: str | None  # set for greeting/thanks/goodbye/unsupported


def _tokens(text: str) -> list[str]:
    return tokenize(text)


def classify_intent(text: str) -> Intent:
    """Classify a message. Pure function; no model, no retrieval."""
    tokens = _tokens(text)
    if not tokens:
        return Intent(name=UNCLEAR, response=None)
    unique = set(tokens)
    if unique <= _GREETING_TOKENS:
        return Intent(name=GREETING, response=RESPONSES[GREETING])
    if unique <= _THANKS_TOKENS and unique & _THANKS_CORE:
        return Intent(name=THANKS, response=RESPONSES[THANKS])
    if unique <= _GOODBYE_TOKENS:
        return Intent(name=GOODBYE, response=RESPONSES[GOODBYE])
    if unique & _UNSUPPORTED_TRIGGERS:
        return Intent(name=UNSUPPORTED_GENERAL, response=RESPONSES[UNSUPPORTED_GENERAL])
    if unique & _AG_SIGNALS:
        return Intent(name=AGRICULTURAL_QUESTION, response=None)
    return Intent(name=UNCLEAR, response=None)
