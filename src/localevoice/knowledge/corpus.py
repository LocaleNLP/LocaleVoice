"""Corpus loading and validation (Milestone 4D schema).

Document schema (all required unless noted): id, title, source_name,
source_url, category, crop_or_species, excerpt, keywords (list, may be
empty), language, date_accessed, review_status. Extra fields (e.g.
usage_or_license_notes, source_updated_at) are preserved untouched.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


REQUIRED_FIELDS = (
    "id",
    "title",
    "source_name",
    "source_url",
    "category",
    "crop_or_species",
    "excerpt",
    "language",
    "date_accessed",
    "review_status",
)

CATEGORIES = (
    "Cereals",
    "Legumes",
    "Animal nutrition",
    "Feed ingredients",
    "Feed by-products",
    "Forage",
    "Livestock",
)


class CorpusError(Exception):
    """Raised when the corpus is missing, malformed, or invalid."""


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    source_name: str
    source_url: str
    category: str
    crop_or_species: str
    excerpt: str
    language: str
    date_accessed: str
    review_status: str
    keywords: tuple[str, ...] = ()
    extra: dict = field(default_factory=dict, compare=False)


def validate_document(record: dict) -> list[str]:
    """Return a list of validation problems (empty means valid)."""
    problems: list[str] = []
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    for name in REQUIRED_FIELDS:
        value = record.get(name)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"missing or empty required field: {name}")
    url = record.get("source_url")
    if isinstance(url, str) and url.strip() and not url.startswith(
        ("http://", "https://")
    ):
        problems.append("source_url must start with http:// or https://")
    category = record.get("category")
    if (
        isinstance(category, str)
        and category.strip()
        and category not in CATEGORIES
    ):
        problems.append(f"category must be one of {list(CATEGORIES)}")
    keywords = record.get("keywords", [])
    if keywords is not None:
        if not isinstance(keywords, list) or not all(
            isinstance(a, str) and a.strip() for a in keywords
        ):
            problems.append("keywords must be a list of non-empty strings")
    return problems


def _to_document(record: dict) -> Document:
    known = set(REQUIRED_FIELDS) | {"keywords"}
    return Document(
        **{name: record[name] for name in REQUIRED_FIELDS},
        keywords=tuple(record.get("keywords") or ()),
        extra={k: v for k, v in record.items() if k not in known},
    )


@dataclass
class Corpus:
    documents: list[Document]
    manifest: dict
    corpus_dir: str

    @property
    def ids(self) -> list[str]:
        return [d.id for d in self.documents]


# Review-status enforcement (Milestone 5.1): only verified excerpts may
# back farmer-facing answers. pending-review / rejected / archived (and
# any unknown status — fail closed) are excluded from evidence
# selection. Diagnostics may still display them, clearly marked.
ELIGIBLE_REVIEW_STATUS = "verified-excerpt"


def is_answer_eligible(doc: Document) -> bool:
    """True only for verified excerpts eligible as answer evidence."""
    return doc.review_status == ELIGIBLE_REVIEW_STATUS


def load_corpus(corpus_dir: str) -> Corpus:
    """Load and validate the corpus in `corpus_dir`.

    Expects `manifest.json` and the JSONL file it names. Raises CorpusError
    on any problem; an empty document list is valid (callers treat it as a
    safe no-evidence state, not as data).
    """
    manifest_path = os.path.join(corpus_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        raise CorpusError(f"Missing corpus manifest: {manifest_path}")
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (ValueError, OSError) as exc:
        raise CorpusError(f"Invalid corpus manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise CorpusError("Corpus manifest must be a JSON object.")

    documents_file = manifest.get("documents_file", "documents.jsonl")
    documents_path = os.path.join(corpus_dir, documents_file)
    if not os.path.isfile(documents_path):
        raise CorpusError(f"Missing corpus documents file: {documents_path}")

    documents: list[Document] = []
    seen: set[str] = set()
    with open(documents_path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError as exc:
                raise CorpusError(
                    f"{documents_file}:{lineno}: invalid JSON: {exc}"
                ) from exc
            problems = validate_document(record)
            if problems:
                raise CorpusError(
                    f"{documents_file}:{lineno}: " + "; ".join(problems)
                )
            doc_id = record["id"]
            if doc_id in seen:
                raise CorpusError(
                    f"{documents_file}:{lineno}: duplicate id: {doc_id}"
                )
            seen.add(doc_id)
            documents.append(_to_document(record))

    declared = manifest.get("documents")
    if isinstance(declared, list) and [d.id for d in documents] != declared:
        raise CorpusError(
            "Manifest 'documents' list does not match documents file order/content."
        )
    return Corpus(documents=documents, manifest=manifest, corpus_dir=corpus_dir)
