#!/usr/bin/env python3
"""Live answer evaluation (Milestone 6D) — MAKES REAL PROVIDER CALLS.

Usage:
  python scripts/evaluate_live_answers.py --dry-run
  python scripts/evaluate_live_answers.py [--output report.json] [--case ID ...]

Dry-run lists the cases without calling any provider. A live run calls
the configured Meta chat model at most once per answerable case
(abstentions and clarifications make no calls). Results are saved as
JSON with per-case retrieval, citations, hygiene, outcome, latency,
and human-review status (always PENDING here).
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from localevoice.evaluation.live import (  # noqa: E402
    evaluate_live_case,
    load_live_cases,
    summarize_live,
    write_live_report,
)
from localevoice.knowledge.corpus import load_corpus  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
DEFAULT_CORPUS_DIR = os.path.join(ROOT, "data", "knowledge")
DEFAULT_CASES = os.path.join(ROOT, "data", "evaluation", "live_cases_6d.json")
DEFAULT_OUT_DIR = os.path.join(ROOT, "data", "evaluation", "live")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--cases", default=DEFAULT_CASES)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--case", action="append", default=[], dest="only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)
    load_dotenv()

    try:
        corpus = load_corpus(args.corpus_dir)
        metadata, cases = load_live_cases(args.cases)
    except Exception as exc:  # noqa: BLE001 - CLI boundary reports and exits
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.only:
        wanted = set(args.only)
        cases = [c for c in cases if c.id in wanted]
        if not cases:
            print(f"ERROR: no cases match {sorted(wanted)}", file=sys.stderr)
            return 1

    if args.dry_run:
        print(f"CASES: {args.cases} (dry run, no provider calls)")
        for case in cases:
            print(f"  {case.id} [{case.section}] expect={case.expected_outcome}")
            print(f"    Q: {case.question}")
        print(f"TOTAL: {len(cases)} cases, 0 provider calls")
        return 0

    from localevoice.providers.meta_chat import chat_complete  # noqa: E402

    print(
        f"LIVE RUN: {len(cases)} cases via the configured Meta chat "
        "model (calls are billable)."
    )
    reports = []
    for case in cases:
        try:
            report = evaluate_live_case(
                case, corpus, chat_fn=chat_complete, top_k=args.top_k
            )
        except Exception as exc:  # noqa: BLE001 - per-case failure recorded
            from localevoice.evaluation.live import LiveCaseReport

            report = LiveCaseReport(
                case_id=case.id,
                section=case.section,
                question=case.question,
                language_inferred=None,
                intent=None,
                retrieved_ids=[],
                eligible_ids=[],
                supplied_ids=[],
                model_called=False,
                raw_response=None,
                outcome="error",
                error={"type": type(exc).__name__, "message": str(exc)},
                expected_outcome=case.expected_outcome,
                outcome_match=False,
            )
        reports.append(report)
        cite = report.citation_containment.get("contained")
        print(
            f"  {report.case_id}: outcome={report.outcome} "
            f"(expected={report.expected_outcome}) "
            f"model_called={report.model_called} "
            f"retrieved={report.retrieved_ids} "
            f"contained={cite} syntax_ok="
            f"{report.citation_syntax.get('syntax_ok')} "
            f"hygiene_clean={report.hygiene.get('clean')} "
            f"ms={report.latency_ms} "
            f"error={report.error['type'] if report.error else None}"
        )

    summary = summarize_live(reports)
    print(f"SUMMARY: {summary}")
    out = args.output
    if out is None:
        os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        out = os.path.join(DEFAULT_OUT_DIR, f"live_6d_{stamp}.json")
    metadata = dict(metadata)
    metadata["mode"] = "live"
    metadata["corpus_version"] = corpus.manifest.get("corpus_version")
    write_live_report(out, metadata, reports)
    print(f"SAVED: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
