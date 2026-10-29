# LocaleVoice — Data and API (Milestone 2)

## 1. External APIs

### 1.1 Meta Model API (chat completions)

- Purpose: grounded answer generation over retrieved evidence.
- Client: OpenAI Python SDK, base URL `https://api.meta.ai/v1`.
- Auth: `MODEL_API_KEY` from the environment.
- Model: `META_CHAT_MODEL=muse-spark-1.3` (confirmed live via the API
  model list and successful requests).
- Single access point: `chat_complete(messages, ...)` in
  `providers/meta_chat.py`; `verify_chat` delegates to it.
- Live behavior verified: grounded Darija answer with citations contained
  in the supplied source IDs; latency and model recorded per run.

### 1.2 Meta Muse Voice Transcribe (speech recognition)

- Purpose: transcribe the user's actual recording.
- Endpoint: `POST https://api.meta.ai/v1/asr/transcribe` (documented
  multipart format).
- Auth: `MODEL_API_KEY` from the environment.
- Model: `META_ASR_MODEL=muse-voice-transcribe-1.0` (confirmed live via
  the API model list; earlier placeholder IDs were rejected with
  `model_not_found`).
- Request shape (all confirmed by live endpoint responses):
  - `request` JSON part: model identifier, mode `PUSH_TO_TALK`,
    `audioEncoding` (`WAV`), optional Arabic language bias.
  - `audio` file part: the WAV bytes (`audio/wav`).
- Response: top-level `transcript` plus a `turns` array (observed live);
  a response with no usable text is a reported failure.
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
| Evidence        | Reference corpus    | Versioned excerpts with provenance (see §3).       |
| Answer          | Chat model          | Shown with sources; failures shown honestly.       |
| Run records     | Pipeline CLI        | Questions, evidence IDs, outputs; no keys.         |
| Eval reports    | Eval runner         | Recall, gating, citations, latency; no keys.       |

## 3. Reference corpus (implemented, version m2-1.0.0)

Location: `data/knowledge/` (`manifest.json` + `documents.jsonl`).

Record format (all fields required unless noted):

- `document_id`, `title`, `publisher`, `source_url`, `retrieved_at`,
  `language`, `crop_or_topic`, `content`, `usage_or_license_notes`
- Optional: `search_aliases` (terms observed verbatim on the source page;
  matching only, not source content), plus extra provenance fields such
  as `source_updated_at`.

Verified contents (retrieved 2026-10-29 via direct HTTPS fetch; short
whitespace-normalized excerpts, no invented text):

| document_id              | source                                              | topic                    |
| ------------------------ | --------------------------------------------------- | ------------------------ |
| feedipedia-cowpea-seeds  | https://www.feedipedia.org/node/232                 | cowpea / ruminant feed   |
| feedipedia-olive-cake    | https://www.feedipedia.org/node/32                  | olive by-products / feed |
| feedipedia-wheat-grain   | https://www.feedipedia.org/node/223                 | wheat grain / feed       |

Publisher for all three: Feedipedia (INRAE, CIRAD, AFZ, FAO). Coverage is
narrow by design; most questions correctly take the insufficient-evidence
path. Retrieval takes reviewed-transcript text and returns ranked passages
or an empty set; never a silent empty answer.

Sources that could not be verified from this environment (FAO pages behind
bot protection, unreachable ministry site) were left out entirely rather
than reconstructed from memory or snippets.

## 4. Evaluation fixtures (implemented, version m2-eval-1.0.0)

Location: `data/evaluation/questions.json`. Six synthetic, manually
authored questions (Arabic-script Darija, Darija/French mixes, one French
control, two unsupported), each with `relevant_doc_ids`,
`expect_insufficient`, `category`, and `human_review` (null = pending).
Explicitly labeled as not real farmer data; they do not establish
real-world language quality.

## 5. Configuration

```
MODEL_API_KEY=<secret, never committed>
META_CHAT_MODEL=muse-spark-1.3
META_ASR_MODEL=muse-voice-transcribe-1.0
LOCALEVOICE_ASR_LANGUAGE_BIAS=<optional, e.g. ar>
```

- `.env.example` carries placeholder values only.
- `.env` is Git-ignored.

## 6. Assumptions

- One API key covers both Meta endpoints.
- Short WAV uploads (tens of seconds).
- Hosted inference only in every milestone.

## 7. Acceptance criteria (Milestone 2)

- Provider modules match the request shapes in sections 1.1–1.2 exactly.
- Corpus validates; every record carries genuine provenance.
- Offline evaluation passes; live evaluation shows citation containment
  and records latency/model.
- Unit tests assert retrieval, gating, and serialization with mocks
  (no network).

## 8. Non-goals

- No corpus expansion beyond the 3 verified excerpts in this milestone.
- No embedding/vector retrieval, no new endpoints, no invented parameters,
  no hardcoded secrets.

## 9. Failure states

- HTTP/API errors: preserve status code and safe diagnostic body/detail;
  redact any key material.
- Malformed or empty responses: raise validation errors, exit nonzero.
- See the shared failure table in `docs/03-app-flow.md`.

## 10. Privacy considerations

- Recordings and transcripts are personal data: transmit only to the
  configured hosted endpoints, keep local copies Git-ignored
  (`data/samples/`), and use fixtures only with explicit approval and
  appropriate consent.
- API keys: environment only; redacted from logs, error messages, run
  records, reports, and docs.
- Corpus excerpts are short attributed passages for prototype evaluation;
  check source terms before redistribution. User data and corpus data
  stay separate.

## 11. Next milestones

- Milestone 3: UI surfaces for transcript review and sourced answers.
- Later: corpus expansion with the same provenance bar, Darija speech
  evaluation.
