# LocaleVoice — Technical Requirements (Milestone 1)

## 1. Stack and constraints

- Python 3.10 or later.
- Hosted inference only; no local model inference.
- Answer generation: Meta Model API.
- Speech recognition experiment: Meta Muse Voice Transcribe.
- Chat client: OpenAI Python SDK with base URL `https://api.meta.ai/v1`.
- Transcription client: `requests` against the documented multipart endpoint
  `POST https://api.meta.ai/v1/asr/transcribe`.
- Configuration: `MODEL_API_KEY`, `META_CHAT_MODEL`, `META_ASR_MODEL` from
  environment (via `python-dotenv`).
- Dependencies: `python-dotenv`, `requests`, `pytest`, plus the OpenAI SDK
  already installed in the project.
- No hardcoded secrets, no invented endpoints. An API call is reported as
  successful only if it actually ran.

## 2. Repository layout (Milestone 1)

```
docs/                       # 01–06 architecture documents (system of record)
src/localevoice/
  __init__.py
  providers/
    __init__.py
    meta_chat.py            # Meta Model API chat provider (OpenAI SDK)
    meta_asr.py             # Meta ASR file-transcription provider (requests)
scripts/
  verify_meta_chat.py       # real hosted chat smoke test
  transcribe_file.py        # real transcription smoke test (PATH_TO_WAV)
tests/
  test_meta_chat.py         # mocked unit tests, no network
  test_meta_asr.py          # mocked unit tests, no network
data/samples/               # Git-ignored; local user-provided audio only
.env.example                # placeholder values, no real secret
README.md                   # exact setup, test, and smoke-test commands
requirements.txt            # pinned install set for this milestone
```

## 3. Chat provider requirements

- Uses the OpenAI Python SDK pointed at base URL `https://api.meta.ai/v1`
  with `MODEL_API_KEY` and model `META_CHAT_MODEL`.
- Exposes one small function that sends a short test prompt asking the
  configured model to return a simple identifiable phrase.
- Failure behavior:
  - Missing key: raise a clear configuration error naming `MODEL_API_KEY`.
  - Request failure: raise an error preserving status code and safe
    diagnostic detail, with no key material.
  - Empty response (no text content): raise an error; never return an empty
    string as a success.

## 4. Transcription provider requirements

- Function signature accepts a filesystem path to a WAV file.
- Input validation before any network call: the path must exist, must be a
  file, and must have a `.wav` extension (case-insensitive).
- Sends a multipart request to `POST https://api.meta.ai/v1/asr/transcribe`:
  - `request` JSON part: model identifier, `PUSH_TO_TALK` mode, WAV encoding,
    plus an optional Arabic language bias when configured.
  - Audio file part: the WAV bytes.
- Parses and validates the real API response; a response with no usable
  transcript text is an error, not a success.
- Errors preserve HTTP status and safe diagnostic detail without leaking the
  API key.
- The optional Arabic language bias must not be described anywhere as
  guaranteed Darija recognition.

## 5. Critical language constraint

- The documented Muse Voice Transcribe language list includes Arabic, but
  does not explicitly list Moroccan Darija as a separate supported language.
- Consequence: Arabic language bias is a hint to the recognizer, not a
  guarantee of dialect support.
- Darija transcription quality must not be reported as validated until real
  Darija recordings have been tested through the smoke test.
- This limitation is recorded here and reflected in the product requirements,
  app flow, data/API notes, and implementation plan.

## 6. Test requirements

- `python -m pytest -q` must run without making live network calls: all unit
  tests mock the SDK/HTTP boundary.
- Unit tests cover, at minimum:
  - Chat: success path returns text; missing key fails; request failure
    preserves diagnostics; empty response fails.
  - ASR: multipart shape (JSON part fields, file part); missing/non-WAV
    input rejected before network; error responses preserve status and
    diagnostics; empty transcript fails.
- Separate smoke tests (outside `pytest`) make real hosted calls:
  - `scripts/verify_meta_chat.py` — real Meta Model API request.
  - `scripts/transcribe_file.py PATH_TO_WAV` — real upload of a
    user-provided recording.
- No mocked response may be presented as a real model result.

## 7. Non-goals for Milestone 1

No retrieval, no agricultural advice generation, no Streamlit UI, no end-user
authentication, no deployment. See `docs/01-product-requirements.md`.

## 8. Assumptions

- `MODEL_API_KEY` from the environment is valid for both Meta endpoints.
- `META_CHAT_MODEL` and `META_ASR_MODEL` values in `.env.example` are
  placeholders/configurable identifiers; exact model IDs must be confirmed
  against current Meta documentation before quality claims are made.
- Short WAV uploads (tens of seconds) for the transcription experiment.

## 9. Acceptance criteria

- `python -m pytest -q` passes with no network access and no paid API call.
- Both smoke scripts run real requests and report real outcomes honestly,
  including failures.
- Error paths carry status/diagnostic detail and never include key material.
- `.env` is Git-ignored; `.env.example` contains no real secret; audio
  fixtures stay out of Git without explicit approval and consent.

## 10. Failure states

Same product failure states as `docs/01-product-requirements.md`, implemented
as typed exceptions (`ConfigurationError`, provider `*Error` types) with safe
messages, raised to the CLI scripts which exit nonzero with a one-line
summary plus safe detail.

## 11. Privacy considerations

- Keys only from the environment; redacted from all logs, messages, and
  tracebacks.
- Recordings are personal data: local handling only, consent-gated fixtures,
  Git-ignored sample directory.

## 12. Next milestones

- Milestone 2: reference corpus plus retrieval and grounded answer generation.
- Milestone 3: Streamlit UI. Later: end-user auth, Darija evaluation,
  deployment. Details in `docs/06-implementation-plan.md`.
