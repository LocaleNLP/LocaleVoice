"""Unit tests for speech-sample evaluation. No providers, no audio needed.

WER/CER tests use synthetic English strings to verify the math only;
they are not language data and prove nothing about Darija quality.
"""

from __future__ import annotations

import json

import pytest

from localevoice.evaluation.speech import (
    cer,
    evaluate_sample,
    load_samples,
    validate_sample,
    wer,
    write_speech_report,
)


def _sample(**overrides):
    record = {
        "sample_id": "dvq-001",
        "consent_status": "granted",
        "permitted_use": "prototype evaluation only",
        "topic": "wheat",
        "intended_language": "moroccan-darija",
    }
    record.update(overrides)
    return record


def test_validate_sample_ok_and_missing_fields():
    assert validate_sample(_sample()) == []
    assert validate_sample("nope") == ["sample is not a JSON object"]
    problems = validate_sample(_sample(sample_id="  "))
    assert any("sample_id" in p for p in problems)
    assert any(
        "consent_status" in p
        for p in validate_sample(_sample(consent_status="maybe"))
    )
    assert validate_sample(_sample(audio_ref=123)) != []


def test_load_samples_roundtrip_and_reject(tmp_path):
    path = tmp_path / "samples.json"
    path.write_text(
        json.dumps({"format_version": "t", "samples": [_sample()]}),
        encoding="utf-8",
    )
    metadata, samples = load_samples(str(path))
    assert metadata["format_version"] == "t"
    assert samples[0]["sample_id"] == "dvq-001"
    path.write_text(
        json.dumps({"samples": [_sample(consent_status="bogus")]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="consent_status"):
        load_samples(str(path))


def test_load_real_samples_file_is_empty():
    _, samples = load_samples("data/evaluation/speech/samples.json")
    assert samples == []


def test_wer_perfect_and_partial():
    assert wer("wheat cattle", "wheat cattle") == 0.0
    assert wer("wheat cattle sheep", "wheat cattle") == pytest.approx(1 / 3)
    assert wer("wheat", "barley") == 1.0


def test_wer_none_without_reference_content():
    assert wer("   ", "wheat") is None
    assert wer("is the", "wheat") is None  # stopwords-only reference


def test_cer_basic_and_empty():
    assert cer("abc", "abc") == 0.0
    assert cer("abc", "abd") == pytest.approx(1 / 3)
    assert cer("   ", "x") is None


def test_evaluate_sample_full_record():
    sample = _sample(
        reference_transcript="wheat cattle",
        asr_transcript="wheat cattle",
        expected_evidence_ids=["doc-1"],
        answer_citations=["doc-1"],
        answer_supplied_ids=["doc-1"],
    )
    report = evaluate_sample(sample, True, retrieved_ids=["doc-1", "doc-2"])
    assert report.usable is True
    assert report.asr["wer"] == 0.0
    assert report.asr["cer"] == 0.0
    assert report.retrieval == {
        "evaluated": True,
        "recalled": True,
        "retrieved_ids": ["doc-1", "doc-2"],
    }
    assert report.grounding["contained"] is True


def test_evaluate_sample_missing_data_yields_nulls_not_zeros():
    report = evaluate_sample(_sample(), False, retrieved_ids=None)
    assert report.usable is False
    assert report.asr["wer"] is None
    assert report.asr["cer"] is None
    assert report.retrieval["evaluated"] is False
    assert report.grounding["evaluated"] is False


def test_evaluate_sample_consent_gates_usability():
    assert (
        evaluate_sample(_sample(consent_status="pending"), True).usable is False
    )
    assert (
        evaluate_sample(_sample(consent_status="withdrawn"), True).usable is False
    )
    assert evaluate_sample(_sample(), False).usable is False


def test_evaluate_sample_grounding_containment_false():
    sample = _sample(
        answer_citations=["invented-id"], answer_supplied_ids=["doc-1"]
    )
    report = evaluate_sample(sample, True)
    assert report.grounding["evaluated"] is True
    assert report.grounding["contained"] is False


def test_write_speech_report_roundtrip(tmp_path):
    report = evaluate_sample(_sample(), False)
    out = str(tmp_path / "speech.json")
    write_speech_report(out, {"mode": "offline"}, [report])
    payload = json.loads(open(out, encoding="utf-8").read())
    assert payload["summary"] == {
        "total": 1,
        "usable": 0,
        "wer_computed": 0,
        "retrieval_evaluated": 0,
        "grounding_evaluated": 0,
    }
    assert "MODEL_API_KEY" not in str(payload)
