# LocaleVoice

Voice-first Moroccan Darija agricultural assistant (hackathon MVP).

Milestone 1 implements the architecture documents plus two real hosted-API
primitives — Meta Model API chat and Meta Muse Voice Transcribe — with
smoke scripts and mocked unit tests. No UI, retrieval, or advice pipeline
yet. The six documents in `docs/` are the system of record.

## Setup

Python 3.10 or later. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set a real MODEL_API_KEY.
```

Confirm the configured model identifiers (`META_CHAT_MODEL`,
`META_ASR_MODEL`) against current Meta documentation.

## Tests (no network, no paid calls)

```bash
python -m pytest -q
```

All unit tests mock the SDK/HTTP boundary, so this needs no API key and no
network access.

## Live smoke tests (real hosted calls)

These make real requests to Meta endpoints and require a valid
`MODEL_API_KEY` in `.env`.

Chat (Meta Model API):

```bash
python scripts/verify_meta_chat.py
```

Transcription (Meta Muse Voice Transcribe, user-provided WAV only):

```bash
python scripts/transcribe_file.py PATH_TO_WAV
```

Optional Arabic recognizer hint (a hint only — not guaranteed Darija
recognition):

```bash
LOCALEVOICE_ASR_LANGUAGE_BIAS=ar python scripts/transcribe_file.py PATH_TO_WAV
```

## Language-coverage note

The documented Muse Voice Transcribe language list includes Arabic but does
not explicitly list Moroccan Darija as a separate supported language.
Arabic bias is a hint, not a guarantee, and Darija quality is unvalidated
until real Darija recordings are tested. See
`docs/02-technical-requirements.md`.

## Layout

- `docs/01-product-requirements.md` … `docs/06-implementation-plan.md`
- `src/localevoice/providers/meta_chat.py` — chat provider
- `src/localevoice/providers/meta_asr.py` — transcription provider
- `scripts/verify_meta_chat.py`, `scripts/transcribe_file.py` — smoke tests
- `tests/` — mocked unit tests
- `data/samples/` — local user-provided audio (Git-ignored, consent-gated)
