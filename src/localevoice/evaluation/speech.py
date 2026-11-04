"""Speech-sample evaluation: ASR, retrieval, and grounding records.

Works over `data/evaluation/speech/samples.json`. All metrics are optional
and computed only when their prerequisites exist:

- WER/CER: only when a human-verified `reference_transcript` is present.
- retrieval: only when `expected_evidence_ids` is present.
- grounding: only when a recorded `answer` with citations is present.

No audio, transcripts, or metrics are ever fabricated. Missing data yields
explicit nulls, never zeros presented as measurements.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

from localevoice.knowledge.retrieve import tokenize

SAMPLES_VERSION = "m4a-speech-1"

REQUIRED_SAMPLE_FIELDS = (
    "sample_id",
    "consent_status",
    "permitted_use",
    "topic",
    "intended_language",
)

CONSENT_STATUSES = ("granted", "pending", "declined", "withdrawn")


def validate_sample(record: dict) -> list[str]:
    """Return validation problems for one speech sample (empty = valid)."""
    problems: list[str] = []
    if not isinstance(record, dict):
        return ["sample is not a JSON object"]
    for name in REQUIRED_SAMPLE_FIELDS:
        value = record.get(name)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"missing or empty required field: {name}")
    consent = record.get("consent_status")
    if (
        isinstance(consent, str)
        and consent.strip()
        and consent not in CONSENT_STATUSES
    ):
        problems.append(f"consent_status must be one of {list(CONSENT_STATUSES)}")
    for name in (
        "audio_ref",
        "reference_transcript",
        "asr_transcript",
        "corrected_transcript",
        "answer_text",
        "usability_notes",
    ):
        value = record.get(name)
        if value is not None and not isinstance(value, str):
            problems.append(f"{name} must be a string or null")
    for name in ("expected_evidence_ids", "answer_citations", "answer_supplied_ids"):
        value = record.get(name)
        if value is not None and not (
            isinstance(value, list) and all(isinstance(v, str) for v in value)
        ):
            problems.append(f"{name} must be a list of strings or null")
    return problems


def load_samples(path: str) -> tuple[dict, list[dict]]:
    """Load samples file; return (metadata, valid sample dicts)."""
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict) or not isinstance(payload.get("samples"), list):
        raise ValueError("samples file must be an object with a samples list")
    samples = []
    for raw in payload["samples"]:
        problems = validate_sample(raw)
        if problems:
            raise ValueError(
                f"sample {raw.get('sample_id', '?')!r}: " + "; ".join(problems)
            )
        samples.append(raw)
    metadata = {k: v for k, v in payload.items() if k != "samples"}
    return metadata, samples


def _levenshtein(a: list[str], b: list[str]) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, start=1):
        cur = [i]
        for j, y in enumerate(b, start=1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def wer(reference: str, hypothesis: str) -> float | None:
    """Word error rate, or None when the reference has no words.

    Normalization: the shared search tokenizer (documented in
    knowledge.retrieve): case/punctuation folding, Arabic diacritic and
    alef folding, definite-article stripping, stopword removal. WER on
    normalized tokens measures content-word recovery, not raw orthography;
    report the normalization alongside any figure.
    """
    ref_tokens = tokenize(reference)
    if not ref_tokens:
        return None
    return _levenshtein(ref_tokens, tokenize(hypothesis)) / len(ref_tokens)


def cer(reference: str, hypothesis: str) -> float | None:
    """Character error rate on whitespace-stripped text, or None if empty."""
    ref = "".join(reference.split())
    if not ref:
        return None
    return _levenshtein(list(ref), list("".join(hypothesis.split()))) / len(ref)


@dataclass
class SpeechItemReport:
    sample_id: str
    consent_status: str
    usable: bool  # consent granted AND audio present
    asr: dict = field(default_factory=dict)
    retrieval: dict = field(default_factory=dict)
    grounding: dict = field(default_factory=dict)
    usability_notes: str | None = None


def evaluate_sample(
    sample: dict,
    audio_exists: bool,
    retrieved_ids: list[str] | None = None,
) -> SpeechItemReport:
    """Evaluate one sample from recorded data (offline; no providers).

    Args:
        sample: validated sample record.
        audio_exists: whether the referenced audio file is present locally.
        retrieved_ids: document IDs retrieved for the corrected (or ASR)
            transcript, or None when retrieval was not run.
    """
    usable = sample["consent_status"] == "granted" and audio_exists
    reference = sample.get("reference_transcript")
    hypothesis = sample.get("corrected_transcript") or sample.get("asr_transcript")

    asr_section: dict = {
        "reference_present": bool(reference and reference.strip()),
        "hypothesis_present": bool(hypothesis and hypothesis.strip()),
        "wer": None,
        "cer": None,
    }
    if reference and reference.strip() and hypothesis and hypothesis.strip():
        asr_section["wer"] = wer(reference, hypothesis)
        asr_section["cer"] = cer(reference, hypothesis)

    expected = sample.get("expected_evidence_ids")
    if expected is None or retrieved_ids is None:
        retrieval_section: dict = {"evaluated": False, "recalled": None}
    else:
        retrieval_section = {
            "evaluated": True,
            "recalled": bool(set(expected) & set(retrieved_ids)),
            "retrieved_ids": retrieved_ids,
        }

    citations = sample.get("answer_citations")
    supplied = sample.get("answer_supplied_ids")
    if citations is None or supplied is None:
        grounding_section: dict = {"evaluated": False, "contained": None}
    else:
        supplied_set = set(supplied)
        grounding_section = {
            "evaluated": True,
            "contained": all(c in supplied_set for c in citations),
            "citations": citations,
        }

    return SpeechItemReport(
        sample_id=sample["sample_id"],
        consent_status=sample["consent_status"],
        usable=usable,
        asr=asr_section,
        retrieval=retrieval_section,
        grounding=grounding_section,
        usability_notes=sample.get("usability_notes"),
    )


def write_speech_report(path: str, metadata: dict, reports: list[SpeechItemReport]) -> None:
    """Write a JSON speech-evaluation report. Contains no API keys."""
    payload = {
        "metadata": metadata,
        "summary": {
            "total": len(reports),
            "usable": sum(1 for r in reports if r.usable),
            "wer_computed": sum(1 for r in reports if r.asr.get("wer") is not None),
            "retrieval_evaluated": sum(1 for r in reports if r.retrieval.get("evaluated")),
            "grounding_evaluated": sum(1 for r in reports if r.grounding.get("evaluated")),
        },
        "items": [asdict(r) for r in reports],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def samples_path(root: str) -> str:
    return os.path.join(root, "data", "evaluation", "speech", "samples.json")
