"""Unit tests for evaluation runner and chat_complete extension. No network."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from localevoice.evaluation.runner import (
    evaluate_all,
    evaluate_item,
    load_fixtures,
    summarize,
    write_report,
)
from localevoice.knowledge.corpus import Corpus, Document
from localevoice.providers.meta_chat import (
    ConfigurationError,
    MetaChatError,
    chat_complete,
    resolve_model,
)


def _doc(doc_id="doc-1", content="Wheat is an energy source for ruminants."):
    return Document(
        document_id=doc_id,
        title="T",
        publisher="P",
        source_url="https://example.org",
        retrieved_at="2026-10-29",
        language="en",
        crop_or_topic="wheat",
        content=content,
        usage_or_license_notes="test",
    )


def _corpus():
    return Corpus(documents=[_doc()], manifest={}, corpus_dir=".")


def _fixtures_file(tmp_path, items):
    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps(
            {"fixtures_version": "t", "items": items}, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    return str(path)


def _item(fx_id="q1", question="wheat?", relevant=("doc-1",), insufficient=False):
    return {
        "id": fx_id,
        "question": question,
        "language_label": "test",
        "relevant_doc_ids": list(relevant),
        "expect_insufficient": insufficient,
        "category": "in-corpus",
    }


def test_load_fixtures_roundtrip(tmp_path):
    _, items = load_fixtures(_fixtures_file(tmp_path, [_item()]))
    assert len(items) == 1
    assert items[0].id == "q1"
    assert items[0].human_review is None


def test_load_fixtures_missing_field(tmp_path):
    bad = _item()
    del bad["question"]
    with pytest.raises(ValueError, match="question"):
        load_fixtures(_fixtures_file(tmp_path, [bad]))


def test_offline_item_recall_and_gate(tmp_path):
    _, (hit, miss) = load_fixtures(
        _fixtures_file(
            tmp_path,
            [
                _item("hit", "wheat?", ("doc-1",), False),
                _item("miss", "capital of Morocco?", (), True),
            ],
        )
    )
    hit_report = evaluate_item(hit, _corpus())
    assert hit_report.relevant_recalled is True
    assert hit_report.insufficient_correct is True
    assert hit_report.citations_within_supplied is None  # offline: n/a
    miss_report = evaluate_item(miss, _corpus())
    assert miss_report.relevant_recalled is True  # nothing expected, none found
    assert miss_report.insufficient_triggered is True
    assert miss_report.insufficient_correct is True


def test_live_item_checks_citation_containment(tmp_path, monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "test-model")
    _, (item,) = load_fixtures(_fixtures_file(tmp_path, [_item()]))
    good = evaluate_item(item, _corpus(), live=True, chat_fn=Mock(return_value="A. [doc-1]"))
    assert good.citations == ["doc-1"]
    assert good.citations_within_supplied is True
    assert good.model == "test-model"
    bad = evaluate_item(
        item, _corpus(), live=True, chat_fn=Mock(return_value="A. [invented-id]")
    )
    assert bad.citations_within_supplied is False


def test_summarize_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "m")
    _, items = load_fixtures(
        _fixtures_file(
            tmp_path,
            [_item("a", "wheat?", ("doc-1",), False), _item("b", "zzz?", (), True)],
        )
    )
    reports = evaluate_all(items, _corpus(), live=True, chat_fn=Mock(return_value="A. [doc-1]"))
    summary = summarize(reports)
    assert summary == {
        "total": 2,
        "relevant_recalled": 2,
        "insufficient_correct": 2,
        "citation_checks": 2,
        "citations_within_supplied": 2,
        "errors": 0,
    }


def test_write_report_roundtrip_without_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "super-secret-key")
    _, items = load_fixtures(_fixtures_file(tmp_path, [_item()]))
    reports = evaluate_all(items, _corpus())
    out = str(tmp_path / "report.json")
    write_report(out, {"mode": "offline"}, reports)
    blob = open(out, encoding="utf-8").read()
    assert "super-secret-key" not in blob
    assert json.loads(blob)["summary"]["total"] == 1


def test_chat_complete_sends_messages():
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[
                    SimpleNamespace(message=SimpleNamespace(content="hi"))
                ]
            )
        )
        text = chat_complete(
            [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
            api_key="k",
            model="m",
        )
    assert text == "hi"
    _, kwargs = mock_client_cls.return_value.chat.completions.create.call_args
    assert kwargs["messages"] == [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u"},
    ]


def test_chat_complete_missing_key_and_empty_response():
    with pytest.raises(ConfigurationError, match="MODEL_API_KEY"):
        chat_complete([{"role": "user", "content": "x"}], api_key="", model="m")
    with patch("openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = (
            SimpleNamespace(choices=[])
        )
        with pytest.raises(MetaChatError, match="no text"):
            chat_complete([{"role": "user", "content": "x"}], api_key="k", model="m")


def test_resolve_model_prefers_argument(monkeypatch):
    monkeypatch.setenv("META_CHAT_MODEL", "env-model")
    assert resolve_model("arg-model") == "arg-model"
    assert resolve_model() == "env-model"
    monkeypatch.delenv("META_CHAT_MODEL", raising=False)
    with pytest.raises(ConfigurationError, match="META_CHAT_MODEL"):
        resolve_model()
