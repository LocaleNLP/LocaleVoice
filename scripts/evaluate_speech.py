#!/usr/bin/env python3
"""Speech-sample evaluation report (offline by default).

Usage:
  python scripts/evaluate_speech.py [--output report.json]
  python scripts/evaluate_speech.py --transcribe [--output report.json]

Offline mode touches no providers: it scores only recorded data (WER/CER
where a human-verified reference exists, retrieval recall where expected
evidence is listed, citation containment where an answer is recorded).

--transcribe makes live ASR calls, but only for samples with granted
consent, present audio, and no recorded asr_transcript yet; results are
saved back into samples.json. Nothing is ever fabricated.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from localevoice.evaluation.speech import (  # noqa: E402
    evaluate_sample,
    load_samples,
    write_speech_report,
)
from localevoice.knowledge.corpus import load_corpus  # noqa: E402
from localevoice.knowledge.retrieve import retrieve  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
SPEECH_DIR = os.path.join(ROOT, "data", "evaluation", "speech")
SAMPLES_FILE = os.path.join(SPEECH_DIR, "samples.json")
CORPUS_DIR = os.path.join(ROOT, "data", "knowledge")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=None)
    parser.add_argument(
        "--transcribe",
        action="store_true",
        help="Live ASR for usable samples missing asr_transcript (saved back).",
    )
    args = parser.parse_args(argv)
    load_dotenv()

    try:
        metadata, samples = load_samples(SAMPLES_FILE)
        corpus = load_corpus(CORPUS_DIR)
    except Exception as exc:  # noqa: BLE001 - CLI boundary reports and exits
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.transcribe:
        from localevoice.providers.meta_asr import (  # noqa: E402
            MetaASRError,
            transcribe_file,
        )

        changed = False
        for sample in samples:
            ref = sample.get("audio_ref")
            audio_path = os.path.join(SPEECH_DIR, ref) if ref else None
            if (
                sample["consent_status"] != "granted"
                or not audio_path
                or not os.path.isfile(audio_path)
                or (sample.get("asr_transcript") or "").strip()
            ):
                continue
            try:
                sample["asr_transcript"] = transcribe_file(audio_path)
                changed = True
                print(f"TRANSCRIBED: {sample['sample_id']}")
            except (MetaASRError, FileNotFoundError, ValueError) as exc:
                print(
                    f"SKIP {sample['sample_id']}: ASR failed: {exc}",
                    file=sys.stderr,
                )
        if changed:
            payload = dict(metadata)
            payload["samples"] = samples
            with open(SAMPLES_FILE, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            print(f"UPDATED: {SAMPLES_FILE}")

    reports = []
    for sample in samples:
        ref = sample.get("audio_ref")
        audio_exists = bool(
            ref and os.path.isfile(os.path.join(SPEECH_DIR, ref))
        )
        text = sample.get("corrected_transcript") or sample.get("asr_transcript")
        retrieved = None
        # No retrieval over non-granted transcripts: declined/withdrawn
        # data must not be evaluated even when it lingers in the file.
        if sample.get("consent_status") == "granted" and text and text.strip():
            retrieved = [
                e.document_id
                for e in retrieve(text, corpus.documents, top_k=3)
            ]
        reports.append(
            evaluate_sample(sample, audio_exists, retrieved_ids=retrieved)
        )

    if args.output:
        metadata = dict(metadata)
        metadata["transcribe_run"] = bool(args.transcribe)
        write_speech_report(args.output, metadata, reports)
        print(f"SAVED: {args.output}")

    usable = sum(1 for r in reports if r.usable)
    scored = sum(1 for r in reports if r.asr.get("wer") is not None)
    print(
        f"SPEECH EVAL: samples={len(reports)} usable={usable} "
        f"wer_computed={scored}"
    )
    for item in reports:
        print(
            f"  {item.sample_id}: usable={item.usable} "
            f"wer={item.asr.get('wer')} cer={item.asr.get('cer')} "
            f"retrieval={item.retrieval} grounding={item.grounding}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
