# LocaleVoice — Data and API (Milestone 1)

## 1. External APIs

### 1.1 Meta Model API (chat completions)

- Purpose: answer generation (Milestone 1: connectivity smoke test only).
- Client: OpenAI Python SDK, base URL `https://api.meta.ai/v1`.
- Auth: `MODEL_API_KEY` from the environment.
- Model: `META_CHAT_MODEL` from the environment (configurable identifier;
  exact value to be confirmed against current Meta documentation).
- Smoke prompt: a short test prompt asking the model to return a simple
  identifiable phrase. Success requires non-empty text content in the
  response; anything else is a reported failure.

### 1.2 Meta Muse Voice Transcribe (speech recognition)

- Purpose: transcribe the user's actual recording.
- Endpoint: `POST https://api.meta.ai/v1/asr/transcribe` (documented
  multipart format).
- Auth: `MODEL_API_KEY` from the environment.
- Request shape:
  - `request` JSON part: model identifier (`META_ASR_MODEL`), mode
    `PUSH_TO_TALK`, WAV encoding, optional Arabic language bias.
  - `audio` file part: the WAV bytes (`audio/wav`). The endpoint
    requires parts named exactly `request` and `audio` (confirmed by a
    live 400 response naming both parts).
- Response: parsed for transcript text; a response with no usable text is a
  reported failure.
- Language coverage: the documented language list includes Arabic but does
  not explicitly list Moroccan Darija as a separate supported language.
  Arabic bias is a hint, not a guarantee. Darija quality is unvalidated
  until real Darija recordings are tested.

## 2. Data handled

| Data            | Source              | Handling (all milestones)                          |
| --------------- | ------------------- | -------------------------------------------------- |
| API key         | `.env` (Git-ignored)| Environment only; never logged, never committed.  |
| Audio recording | User-provided       | Sent to hosted ASR; local copies Git-ignored.      |
| Transcript      | ASR + user edits    | User data; shown for review before any retrieval.  |
| Evidence        | Reference corpus    | Milestone 2+; curated, sourced passages.           |
| Answer          | Chat model          | Shown with sources; failures shown honestly.       |

## 3. Reference corpus (Milestone 2+, design notes only)

- A small curated set of agricultural reference passages relevant to
  Moroccan farming, each with a stable source identifier (title + origin).
- Retrieval takes the reviewed transcript and returns ranked passages or an
  explicit no-evidence outcome; no silent empty answers.
- Corpus content decisions (topics, licensing, language) belong to
  Milestone 2; this milestone only requires that answers later be traceable
  to cited passages.

## 4. Configuration

```
MODEL_API_KEY=<secret, never committed>
META_CHAT_MODEL=<configurable chat model identifier>
META_ASR_MODEL=<configurable ASR model identifier>
LOCALEVOICE_ASR_LANGUAGE_BIAS=<optional, e.g. ar>
```

- `.env.example` carries placeholder values only.
- `.env` is Git-ignored.
- `META_ASR_MODEL=muse-voice-transcribe-1.0` and
  `META_CHAT_MODEL=muse-spark-1.3` were confirmed live via the API model list
  and successful requests. The `request` JSON part uses `audioEncoding`
  (confirmed by a live 400 naming the field), and the ASR response carries
  a top-level `transcript` plus a `turns` array. Darija quality remains
  unvalidated pending real recordings.

## 5. Assumptions

- One API key covers both Meta endpoints.
- Short WAV uploads (tens of seconds).
- Hosted inference only in every milestone.

## 6. Acceptance criteria (Milestone 1)

- Provider modules match the request shapes in sections 1.1–1.2 exactly.
- Smoke scripts exercise the real endpoints and validate real responses.
- Unit tests assert the multipart/request shapes with mocks (no network).

## 7. Non-goals

- No corpus ingestion, retrieval index, or advice pipeline in this milestone.
- No new endpoints, no invented parameters, no hardcoded secrets.

## 8. Failure states

- HTTP/API errors: preserve status code and safe diagnostic body/detail;
  redact any key material.
- Malformed or empty responses: raise validation errors, exit nonzero.
- See the shared failure table in `docs/03-app-flow.md`.

## 9. Privacy considerations

- Recordings and transcripts are personal data: transmit only to the
  configured hosted endpoints, keep local copies Git-ignored
  (`data/samples/`), and use fixtures only with explicit approval and
  appropriate consent.
- API keys: environment only; redacted from logs, error messages, and docs.
- Future corpus content must be licensed for this use; user data and corpus
  data stay separate.

## 10. Next milestones

- Milestone 2: corpus curation plus retrieval and grounded generation.
- Milestone 3: UI surfaces for transcript review and sourced answers.
