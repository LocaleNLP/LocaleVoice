"""Unit tests for corpus loading and validation. No network access."""

from __future__ import annotations

import json

import pytest

from localevoice.knowledge.corpus import (
    CorpusError,
    load_corpus,
    validate_document,
)


def _doc(**overrides):
    record = {
        "document_id": "doc-1",
        "title": "Title",
        "publisher": "Publisher",
        "source_url": "https://example.org/doc-1",
        "retrieved_at": "2026-10-29",
        "language": "en",
        "crop_or_topic": "wheat",
        "content": "Wheat content here.",
        "usage_or_license_notes": "Prototype excerpt.",
    }
    record.update(overrides)
    return record


def _write_corpus(tmp_path, records, manifest_docs=None):
    docs_path = tmp_path / "documents.jsonl"
    docs_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8",
    )
    manifest = {
        "corpus_version": "test-1",
        "documents_file": "documents.jsonl",
        "documents": (
            manifest_docs
            if manifest_docs is not None
            else [r["document_id"] for r in records]
        ),
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return str(tmp_path)


def test_load_valid_corpus(tmp_path):
    corpus_dir = _write_corpus(tmp_path, [_doc(), _doc(document_id="doc-2")])
    corpus = load_corpus(corpus_dir)
    assert corpus.ids == ["doc-1", "doc-2"]
    assert corpus.manifest["corpus_version"] == "test-1"
    assert corpus.documents[0].content == "Wheat content here."


def test_load_empty_corpus_is_valid(tmp_path):
    corpus = load_corpus(_write_corpus(tmp_path, []))
    assert corpus.documents == []


def test_missing_manifest_fails(tmp_path):
    with pytest.raises(CorpusError, match="manifest"):
        load_corpus(str(tmp_path))


def test_malformed_json_line_fails(tmp_path):
    docs_path = tmp_path / "documents.jsonl"
    docs_path.write_text("{not json\n", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"documents_file": "documents.jsonl"})
    )
    with pytest.raises(CorpusError, match="invalid JSON"):
        load_corpus(str(tmp_path))


def test_missing_required_field_fails(tmp_path):
    record = _doc()
    del record["source_url"]
    with pytest.raises(CorpusError, match="source_url"):
        load_corpus(_write_corpus(tmp_path, [record]))


def test_empty_content_fails(tmp_path):
    with pytest.raises(CorpusError, match="content"):
        load_corpus(_write_corpus(tmp_path, [_doc(content="   ")]))


def test_bad_source_url_fails(tmp_path):
    with pytest.raises(CorpusError, match="source_url"):
        load_corpus(_write_corpus(tmp_path, [_doc(source_url="not-a-url")]))


def test_duplicate_document_id_fails(tmp_path):
    with pytest.raises(CorpusError, match="duplicate"):
        load_corpus(_write_corpus(tmp_path, [_doc(), _doc()]))


def test_manifest_mismatch_fails(tmp_path):
    with pytest.raises(CorpusError, match="Manifest"):
        load_corpus(
            _write_corpus(tmp_path, [_doc()], manifest_docs=["other-id"])
        )


def test_validate_document_reports_problems():
    assert validate_document(_doc()) == []
    assert validate_document("nope") == ["record is not a JSON object"]
    problems = validate_document(_doc(title="", content=""))
    assert "missing or empty required field: title" in problems
    assert "missing or empty required field: content" in problems
    assert validate_document(_doc(search_aliases=["ok", ""])) != []


def test_real_corpus_loads():
    corpus = load_corpus("data/knowledge")
    assert len(corpus.documents) == 3
    assert all(d.source_url.startswith("https://") for d in corpus.documents)
