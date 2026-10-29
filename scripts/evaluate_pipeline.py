#!/usr/bin/env python3
"""Run the versioned evaluation fixtures (offline by default, no API calls).

Usage: python scripts/evaluate_pipeline.py [--live] [--output report.json]

Offline mode checks retrieval recall and the insufficient-evidence gate.
--live also generates real Meta answers and checks citation containment.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from localevoice.evaluation.runner import (  # noqa: E402
    evaluate_all,
    load_fixtures,
    summarize,
    write_report,
)
from localevoice.knowledge.corpus import load_corpus  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
DEFAULT_CORPUS_DIR = os.path.join(ROOT, "data", "knowledge")
DEFAULT_FIXTURES = os.path.join(ROOT, "data", "evaluation", "questions.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--fixtures", default=DEFAULT_FIXTURES)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)
    load_dotenv()

    try:
        corpus = load_corpus(args.corpus_dir)
        metadata, fixtures = load_fixtures(args.fixtures)
    except Exception as exc:  # noqa: BLE001 - CLI boundary reports and exits
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    reports = evaluate_all(fixtures, corpus, top_k=args.top_k, live=args.live)
    summary = summarize(reports)
    print(f"MODE: {'live' if args.live else 'offline'}")
    print(f"FIXTURES: {args.fixtures}")
    print(
        f"SUMMARY: recalled={summary['relevant_recalled']}/{summary['total']} "
        f"insufficient_correct={summary['insufficient_correct']}/{summary['total']} "
        f"citations_ok={summary['citations_within_supplied']}/"
        f"{summary['citation_checks']} errors={summary['errors']}"
    )
    for item in reports:
        cite = (
            "citations=n/a"
            if item.citations_within_supplied is None
            else f"citations_ok={item.citations_within_supplied} cited={item.citations}"
        )
        print(
            f"  {item.id}: recalled={item.relevant_recalled} "
            f"insufficient={item.insufficient_triggered} "
            f"(expected={item.insufficient_expected}) "
            f"retrieved={item.retrieved_ids} {cite} "
            f"model={item.model} ms={item.elapsed_ms} "
            f"human_review={'pending' if item.human_review is None else 'recorded'}"
        )
    if args.output:
        metadata = dict(metadata)
        metadata["mode"] = "live" if args.live else "offline"
        metadata["corpus_version"] = corpus.manifest.get("corpus_version")
        write_report(args.output, metadata, reports)
        print(f"SAVED: {args.output}")
    failed = [r for r in reports if not r.insufficient_correct or r.error]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
