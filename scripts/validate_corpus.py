#!/usr/bin/env python3
"""Validate the knowledge corpus schema and manifest consistency.

Usage: python scripts/validate_corpus.py [--corpus-dir data/knowledge]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from localevoice.knowledge.corpus import CorpusError, load_corpus  # noqa: E402

DEFAULT_CORPUS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowledge"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR)
    args = parser.parse_args(argv)
    try:
        corpus = load_corpus(args.corpus_dir)
    except CorpusError as exc:
        print(f"CORPUS INVALID: {exc}", file=sys.stderr)
        return 1
    print(
        f"CORPUS VALID: {len(corpus.documents)} documents "
        f"(version {corpus.manifest.get('corpus_version')})"
    )
    for doc in corpus.documents:
        print(f"  - {doc.document_id}: {doc.title} [{doc.language}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
