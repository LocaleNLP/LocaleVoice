#!/usr/bin/env python3
"""Real hosted chat smoke test: Meta Model API.

Makes one live request and prints the real model text. Exits nonzero on any
failure (missing key, request error, empty response). Never prints the key.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from localevoice.providers.meta_chat import (  # noqa: E402
    SMOKE_EXPECTED_PHRASE,
    ConfigurationError,
    MetaChatError,
    verify_chat,
)


def main() -> int:
    load_dotenv()
    try:
        text = verify_chat()
    except (ConfigurationError, MetaChatError) as exc:
        print(f"CHAT SMOKE TEST FAILED: {exc}", file=sys.stderr)
        return 1
    print("CHAT SMOKE TEST OK: received a real hosted response.")
    print(f"MODEL: {os.environ.get('META_CHAT_MODEL', '(unset)')}")
    print(f"RESPONSE: {text}")
    if SMOKE_EXPECTED_PHRASE in text:
        print(f"EXPECTED PHRASE PRESENT: {SMOKE_EXPECTED_PHRASE}")
    else:
        print(
            "NOTE: response did not contain the expected phrase; "
            "the request itself succeeded."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
