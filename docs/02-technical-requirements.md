# LocaleVoice — Technical Requirements (Milestone 3)

## 1. Stack and constraints

- Python 3.10 or later.
- Hosted inference only; no local model inference.
- Answer generation: Meta Model API (`META_CHAT_MODEL=muse-spark-1.3`,
  confirmed live).
- Speech recognition experiment: Meta Muse Voice Transcribe
  (`META_ASR_MODEL=muse-voice-transcribe-1.0`, confirmed live).
- Chat client: OpenAI Python SDK with base URL `https://api.meta.ai/v1`.
- Transcription client: `requests` against the documented multipart endpoint
  `POST https://api.meta.ai/v1/asr/transcribe`.
- Configuration: `MODEL_API_KEY`, `META_CHAT_MODEL`, `META_ASR_MODEL` from
  environment (via `python-dotenv`).
- Dependencies: `python-dotenv`, `requests`, `pytest`, plus the OpenAI SDK
  already installed in the project.
- No hardcoded secrets, no invented endpoints. An API call is reported as
  successful only if it actually ran.

## 2. Repository layout (Milestone 3)

```
app.py                      # Streamlit UI (thin layer over the backend)
.streamlit/config.toml      # obsidian/sand/neon-lime theme
docs/                       # 01–06 architecture documents (system of record)
src/localevoice/
  providers/
    meta_chat.py            # single source for Meta chat (chat_complete + verify_chat)
    meta_asr.py             # Meta ASR file-transcription provider (requests)
  knowledge/
    corpus.py               # corpus loading + schema validation
    retrieve.py             # deterministic lexical retrieval baseline
  pipeline/
    answer.py               # orchestration + grounded generation + run records
    intent.py               # deterministic intent routing (no model calls)
    trace.py                # evidence traces + citation validation
  evaluation/
    runner.py               # offline/live fixture evaluation + reports
    speech.py               # speech-sample eval (WER/CER gated on references)
  ui/
    flow.py                 # UI orchestration (no Streamlit imports; tested)
scripts/
  verify_meta_chat.py       # real hosted chat smoke test
  transcribe_file.py        # real transcription smoke test (PATH_TO_WAV)
  answer_question.py        # CLI vertical slice (--question ...)
  evaluate_pipeline.py      # offline/live evaluation runner
  validate_corpus.py        # corpus schema validation
  evaluate_speech.py        # speech-sample eval (offline + opt-in transcribe)
tests/                      # mocked unit tests, no network (183 tests)
data/
  knowledge/                # manifest.json + documents.jsonl (versioned corpus)
  evaluation/               # questions.json + speech/ samples (versioned)
  samples/                  # Git-ignored; local user-provided audio only
.env.example                # placeholder values, no real secret
README.md                   # exact setup, test, and smoke-test commands
requirements.txt            # pinned install set
```

## 3. Chat provider requirements

- Uses the OpenAI Python SDK pointed at base URL `https://api.meta.ai/v1`
  with `MODEL_API_KEY` and model `META_CHAT_MODEL`.
- `chat_complete(messages, ...)` is the single source for Meta chat access;
  `verify_chat(prompt, ...)` delegates to it with one user message. The
  request format is unchanged from Milestone 1.
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
  - `request` JSON part: model identifier, `PUSH_TO_TALK` mode,
    `audioEncoding` (`WAV`), plus an optional Arabic language bias when
    configured. (Field name `audioEncoding` and part names `request`/`audio`
    were confirmed by live endpoint errors during Milestone 1.)
  - `audio` file part: the WAV bytes (`audio/wav`).
- Parses and validates the real API response (top-level `transcript` plus a
  `turns` array, as observed live); a response with no usable transcript
  text is an error, not a success.
- Errors preserve HTTP status and safe diagnostic detail without leaking the
  API key.
- The optional Arabic language bias must not be described anywhere as
  guaranteed Darija recognition.

## 5. Corpus and retrieval requirements

- Corpus schema, Milestone 4D (see `docs/05-data-and-api.md`): `id`,
  `title`, `source_name`, `source_url`, `category`, `crop_or_species`,
  `excerpt`, `keywords`, `language`, `date_accessed`, `review_status`.
  Internal retrieval views keep the stable `document_id` naming.
- `load_corpus` validates every record and the manifest; malformed data
  raises `CorpusError`. An empty corpus loads fine and is treated by
  callers as a safe no-answer state.
- Retrieval is a deterministic lexical baseline: score = distinct query
  tokens matched; ties broken by `document_id`; only score > 0 returned.
  An opt-in `weighting="idf"` mode re-ranks by IDF-weighted sums for
  comparison; the count baseline stays the default.
- Search-only normalization (documented in code): NFKC fold, strip Arabic
  diacritics/tatweel, alef/ة/ى folding, hamza folding (ؤ→و, ئ→ي),
  Arabic definite-article stripping, Latin lowercasing, punctuation
  removal (including Arabic ؟،؛), single-character token drop, and a
  minimal documented stopword filter (Milestone 4A precision fix:
  without it, English function words matched every English document).
- Thresholds are explicit and caller-configurable: `top_k` caps
  returned evidence; `min_score` gates relevance (CLI `--min-score`).
- The original query string is never modified. Retrieval claims no Darija
  semantic understanding.

## 6. Pipeline and evaluation requirements

- `answer_question` classifies intent first (deterministic, no model):
  social intents resolve instantly; unsupported-domain abstains with
  its own message; otherwise it retrieves, and with no relevant
  evidence (score below `min_score`) returns the insufficient-evidence
  message or a targeted clarification, with no model call.
- Generation prompt treats supplied evidence as the only factual basis,
  requires `[document_id]` citations, forbids invented sources, prefers
  concise Darija for Darija questions, preserves uncertainty, asks for
  missing context, and avoids chemical/dosage instructions.
- `AnswerResult` carries answer text, language info (requested/inferred with
  uncertainty), supplied source IDs, evidence with scores, the
  insufficient-evidence flag, model ID, elapsed time, error detail,
  intent, and a secret-free evidence trace. Citation containment is
  validated post-generation and reported; containment is not a claim
  of independent factual verification.
- `to_run_record()` serializes everything storable with no secrets.
- Evaluation fixtures are versioned, synthetic, and explicitly labeled as
  not real farmer data. Offline mode checks recall + gating; live mode
  adds citation containment, latency, and model ID. Human language-quality
  review stays a separate explicit field (`human_review`, null = pending).
- No WER/CER figures anywhere: they require real audio plus reference
  transcripts, which do not exist yet.

## 7. Critical language constraint

- The documented Muse Voice Transcribe language list includes Arabic, but
  does not explicitly list Moroccan Darija as a separate supported language.
- Consequence: Arabic language bias is a hint to the recognizer, not a
  guarantee of dialect support.
- Darija transcription quality must not be reported as validated until real
  Darija recordings have been tested through the smoke test.
- This limitation is recorded here and reflected in the product requirements,
  app flow, data/API notes, and implementation plan.

## 8. Test requirements

- `python -m pytest -q` must run without making live network calls: all unit
  tests mock the SDK/HTTP boundary (183 tests, Milestone 4D), including
  headless AppTest UI flows (mocked providers; not browser verification).
- Unit tests cover corpus validation, normalization, French/Arabic/mixed
  search, ranking, no-match and empty behavior, prompt construction,
  citation extraction, insufficient-evidence gating, provider errors,
  secret-free serialization, and all Milestone 1 regressions.
- Separate live checks (outside `pytest`): chat smoke test, ASR smoke test,
  `answer_question.py` grounded run, `evaluate_pipeline.py --live`.
- No mocked response may be presented as a real model result.

## 9. Non-goals for Milestone 3

No end-user authentication, no deployment, no embedding retrieval, no
language-quality claims. In-browser verification of the app is pending
(sandbox blocked server sockets; see `docs/06-implementation-plan.md`).
See `docs/01-product-requirements.md`.

## 10. Assumptions

- `MODEL_API_KEY` from the environment is valid for both Meta endpoints.
- Exactly three verified corpus excerpts; most questions correctly take
  the insufficient-evidence path.
- Short WAV uploads (tens of seconds) for the transcription experiment.

## 11. UI rendering rule (Milestone 4A)

Transcripts and answers are untrusted text and must be HTML-escaped
before rendering (`safe_html_paragraph` in `ui/flow.py`); raw
interpolation into `unsafe_allow_html` markup is a defect.

## 11b. Acceptance criteria

- `python -m pytest -q` passes with no network access and no paid API call.
- Corpus validates; offline evaluation passes on all fixtures.
- Live grounded answer and live evaluation ran against the real hosted
  model with citations contained in supplied IDs.
- Error paths carry status/diagnostic detail and never include key material.
- `.env` is Git-ignored; `.env.example` contains no real secret; audio
  fixtures stay out of Git without explicit approval and consent.

## 12. Failure states

Per `docs/01-product-requirements.md` plus typed pipeline behavior:
missing key, invalid audio, network/API errors, empty responses, and empty
corpora are explicit nonzero-exit failures; missing evidence is a valid
insufficient-evidence result (exit 0).

## 13. Privacy considerations

- Keys only from the environment; redacted from all logs, messages, run
  records, reports, and tracebacks.
- Recordings are personal data: local handling only, consent-gated fixtures,
  Git-ignored sample directory.
- Corpus excerpts are short attributed passages; check source terms before
  redistribution.

## 14. Next milestones

- Milestone 3: Streamlit UI — done. Milestone 4: real-user validation
  and hardening. Later: end-user auth, deployment. Details in
  `docs/06-implementation-plan.md`.
