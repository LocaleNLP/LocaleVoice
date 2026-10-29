#!/usr/bin/env python3
"""Real transcription smoke test: Meta Muse Voice Transcribe.

Usage: python scripts/transcribe_file.py PATH_TO_WAV

Uploads an actual user-provided WAV recording and prints the real transcript.
Exits nonzero on any failure. Never prints the key. Use only recordings you
are explicitly permitted to share for testing.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from localevoice.providers.meta_asr import MetaASRError, transcribe_file  # noqa: E402


def main(argv: list[str]) -> int:
    load_dotenv()
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        transcript = transcribe_file(argv[1])
    except (FileNotFoundError, ValueError, MetaASRError) as exc:
        print(f"ASR SMOKE TEST FAILED: {exc}", file=sys.stderr)
        return 1
    print("ASR SMOKE TEST OK: received a real hosted transcript.")
    print(f"MODEL: {os.environ.get('META_ASR_MODEL', '(unset)')}")
    print(f"TRANSCRIPT: {transcript}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
