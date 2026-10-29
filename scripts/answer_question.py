#!/usr/bin/env python3
"""Ask a farming question; retrieve evidence and generate a grounded answer.

Usage: python scripts/answer_question.py --question "..." [--top-k 3]
       [--language darija] [--save run.json]

A live Meta API call is made only when relevant evidence is found.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from localevoice.knowledge.corpus import CorpusError, load_corpus  # noqa: E402
from localevoice.pipeline.answer import answer_question  # noqa: E402

DEFAULT_CORPUS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowledge"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True, help="Farming question.")
    parser.add_argument(
        "--language", default=None, help="Requested answer language/script."
    )
    parser.add_argument("--top-k", type=int, default=3, help="Retrieval limit.")
    parser.add_argument(
        "--corpus-dir", default=DEFAULT_CORPUS_DIR, help="Corpus directory."
    )
    parser.add_argument(
        "--save", default=None, help="Write the run record JSON here."
    )
    args = parser.parse_args(argv)
    load_dotenv()

    try:
        corpus = load_corpus(args.corpus_dir)
    except CorpusError as exc:
        print(f"ERROR: cannot load corpus: {exc}", file=sys.stderr)
        return 1
    if not corpus.documents:
        print("ERROR: corpus is empty; no answer can be generated.", file=sys.stderr)
        return 1

    try:
        result = answer_question(
            args.question,
            corpus,
            top_k=args.top_k,
            language=args.language,
        )
    except (ValueError, CorpusError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"QUESTION: {result.question}")
    lang = result.language
    print(
        f"LANGUAGE: inferred={lang.inferred} "
        f"requested={lang.requested} uncertain={lang.uncertain}"
    )
    print(f"INSUFFICIENT_EVIDENCE: {result.insufficient_evidence}")
    if result.model:
        print(f"MODEL: {result.model} ELAPSED_MS: {result.elapsed_ms}")
    if result.evidence:
        print("EVIDENCE:")
        for item in result.evidence:
            print(
                f"  - [{item['document_id']}] score={item['score']} "
                f"matched={','.join(item['matched_terms'])}"
            )
            print(f"    {item['title']} ({item['publisher']})")
    else:
        print("EVIDENCE: none")
    print("ANSWER:")
    print(result.answer_text)
    if result.error:
        print(f"ERROR_DETAIL: {result.error['type']}: {result.error['message']}")
        return 1

    if args.save:
        record = result.to_run_record()
        record["corpus_version"] = corpus.manifest.get("corpus_version")
        with open(args.save, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
        print(f"SAVED: {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
