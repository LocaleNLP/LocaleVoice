# LocaleVoice — Implementation Plan (Milestone 4C)

## 0c. Milestone 4C work items — human validation readiness audit (done)

1. Baseline 137 passed; offline eval 6/6; speech eval 0 samples.
   Verified the conversation state machine by reading plus tests:
   failed retries roll back without duplicating turns/responses/
   context (new integrity test: fail-fail-succeed), closed
   conversations reject responses, empty input changes nothing.
2. Browser checklist reviewed against app.py: fixed 3 inaccuracies
   (upload playback now implemented via `st.audio`; Confirm may land
   on the clarify stage; live-call steps labeled) and extended to 13
   steps (empty-text, multi-response, restart). Status honestly
   recorded: all BLOCKED here, none run in a browser.
3. Darija review package `docs/08-darija-language-review.md`: all 10
   user-facing strings extracted verbatim with meanings, correction
   space, and PENDING approval. No wording rewritten.
4. Speech readiness verified: consent-gated, audio Git-ignored and
   absent, WER/CER null without references, missing-vs-zero kept
   distinct, no performance claims anywhere.
5. Human validation protocol `docs/09-human-validation-protocol.md`:
   6 scenarios, per-scenario capture sheet, separate
   correctness/language/usefulness axes, stop rules. No round run yet.
6. Reconciled test counts to the final suite number across README
   and docs 01–02.

## 0b. Milestone 4B work items — multi-turn clarification (done)

1. Added `pipeline/conversation.py`: explicit `Conversation` state
   (id, original question, category, turns, asked clarifications,
   responses, accumulated context, evidence, status, result) with
   `start_conversation`, `respond_to_clarification` (retry over
   original + all context), and `finish_conversation`.
2. Grounding preserved: `answer_question` untouched; answers only on
   retrieved evidence; clarification turns never call the model; error
   retries roll back the failed turn; still-missing abstention uses
   per-category messages in `clarify.STILL_MISSING` (Darija wording
   flagged HUMAN REVIEW PENDING, centralized in `clarify.py`).
3. UI: new `clarify` stage (original question, conversation trace,
   reply form with clear-on-submit, finish/start-over); answer stage
   shows the trace expander. Fixed duplicate Streamlit button IDs
   (unique keys) found by the new AppTest tests.
4. Tests: 19 new (17 conversation + 2 AppTest clarify flows); final
   suite 137 passed. Five simulated traces produced with mocked chat.
5. No corpus change, no retriever replacement, no Darija audio
   collected, no browser verification claimed.

## 0a. Milestone 4A work items — browser verification + Darija eval readiness (done)

## 0a. Milestone 4A work items — browser verification + Darija eval readiness (done)

1. Audited repo at 82-test baseline (exit 0); preserved all uncommitted
   Milestone 3 work; confirmed backend signatures and WAV-only ASR input.
2. Browser verification: BLOCKED in this environment (sandbox denies
   socket binds, so the Streamlit server cannot start; no browser or
   automation tooling installed). No browser claim is made. Added a
   reproducible 9-step manual checklist to README instead.
3. Added headless UI regression tests (`tests/test_app.py`, Streamlit
   AppTest, mocked HTTP boundary): startup, upload->review->answer,
   edit-before-confirm, typed fallback, insufficient path, ASR/chat
   failures, retry/reset. Labeled as not browser verification.
4. Demonstrated retrieval precision defect via the new tests (English
   stopword overlap retrieved every English doc); fixed with a
   documented minimal stopword filter + Arabic punctuation handling in
   `retrieve.py`, with regression tests. Offline eval still 6/6.
5. Built the consent-based speech-eval workflow:
   `data/evaluation/speech/{samples.json,README.md}` (empty, no data),
   `src/localevoice/evaluation/speech.py` (validation, WER/CER gated on
   human references, separate ASR/retrieval/grounding sections),
   `scripts/evaluate_speech.py` (offline report + opt-in `--transcribe`
   for consented audio only). Audio dir Git-ignored.
6. Reliability/privacy review: fixed unescaped transcript/answer HTML
   rendering (`safe_html_paragraph`, tested); hardened temp-file fd
   cleanup on write failure (tested cleanup on success/failure);
   confirmed 10 MiB cap, provider timeouts, key redaction, no audio
   logging. No evidence-gating change.
7. Live re-verification after changes: chat smoke OK (exit 0), Darija
   wheat question grounded on `feedipedia-wheat-grain` (exit 0).
   No Darija audio collected; no WER/CER computed.
8. Final: 109 tests pass (exit 0); updated README and docs.

## 0. Milestone 3 work items (done)

1. Audited the repository (65-test baseline, exit 0); confirmed backend
   signatures and the WAV-only ASR input requirement from the provider code.
2. Added `src/localevoice/ui/flow.py`: upload validation (WAV/RIFF/size),
   temp-file transcription handoff, confirmed-text answering. No Streamlit
   imports; backend functions injectable for offline tests.
3. Built `app.py`: Ask (upload + `st.audio_input` + typed fallback),
   Review (recognized vs corrected transcript, mandatory gate), Answer
   (answer + source expanders + model/latency), Failure (message +
   collapsible detail + retry/start-over). Obsidian/sand/neon-lime theme.
4. Backend untouched except `requirements.txt` (+streamlit): no logic
   duplicated, gating unchanged, no fabricated outputs.
5. Added 17 UI orchestration tests (82 total), all offline with mocks.
6. Verified live: real French TTS speech WAV -> real ASR transcript ->
   retrieved `feedipedia-wheat-grain` -> grounded cited answer (exit 0).
   Verified all app stages execute headlessly and all widget APIs exist
   in the installed Streamlit. A server boot + browser check was not
   possible in this sandbox (socket bind denied); the user runs
   `streamlit run app.py` locally.
7. Updated README and docs 01–06.

## 1. Milestone 2 work items (done)

1. Audited Milestone 1 (docs, code, tests); baseline 21 passing tests,
   live chat smoke success, live-validated ASR request shape.
2. Attempted authoritative sourcing; retrieved 3 genuine Feedipedia
   excerpts with provenance (FAO/minstry sources that blocked automated
   fetch were excluded, not reconstructed).
3. Built `data/knowledge/` (manifest + JSONL, version m2-1.0.0) and
   `data/evaluation/` (6 synthetic fixtures, version m2-eval-1.0.0).
4. Implemented `knowledge/` (loading, validation, lexical retrieval),
   `pipeline/` (grounded generation, run records), `evaluation/`
   (offline/live runner, reports).
5. Extended `providers/meta_chat.py` with `chat_complete` as the single
   chat source; `verify_chat` delegates unchanged (no request-format
   change; all 21 Milestone 1 tests still pass).
6. Added `scripts/answer_question.py`, `scripts/evaluate_pipeline.py`,
   `scripts/validate_corpus.py`.
7. Added 44 unit tests (65 total), all offline with mocked chat.
8. Ran live grounded answer (Darija, cited, exit 0), no-evidence check
   (exit 0, no model call), and live evaluation (6/6 recall, 6/6 gating,
   6/6 citation containment, 0 errors).
9. Updated all six documents and `README.md`.

## 2. Milestone 2 acceptance criteria

- `python -m pytest -q` passes with no live network calls.
- Corpus validates; offline evaluation passes on all fixtures.
- Real Meta-generated answer tested with citations inside supplied IDs.
- No-evidence path tested with no model call.
- Errors preserve status/diagnostics without leaking keys.
- No mocked response presented as a real model result.
- Real Darija ASR quality still pending (no consented speech tested);
  documented, not claimed.

## 3. Non-goals (Milestone 2)

No Streamlit UI, end-user authentication, deployment, embedding
retrieval, or language-quality claims.

## 4. Assumptions

- Python 3.10+; hosted inference only.
- `MODEL_API_KEY`, `META_CHAT_MODEL`, `META_ASR_MODEL` from the environment.
- Narrow verified corpus; lexical baseline; synthetic fixtures.

## 5. Failure states

Per `docs/03-app-flow.md`: missing key, invalid audio, network/API
errors, empty responses, and empty corpora are explicit failures;
missing evidence is a valid exit-0 insufficient-evidence result.

## 6. Privacy considerations

Per `docs/05-data-and-api.md`: Git-ignored `.env` and sample audio,
consent-gated fixtures, redacted keys, secret-free run records.

## 7. Next milestones

### Milestone 3 — Streamlit voice-first UI (done, this milestone)

See section 0. Still no end-user auth, no deployment.

### Milestone 4A — Browser verification + Darija eval readiness (done)

See section 0a. Browser verification itself remains BLOCKED here; the
manual checklist in README is the handoff.

### Milestone 4B — Multi-turn clarification (done, this milestone)

See section 0b.

### Milestone 4C — Human validation and readiness audit (done)

See section 0c. Preparation only: no browser session, no review, no
round, and no audio were completed in this milestone.

### Milestone 4D — First human validation round (single next milestone)

- A person runs the README browser checklist (desktop + mobile),
  including the multi-turn conversation steps, and records PASS/FAIL.
- Darija speaker completes `docs/08-darija-language-review.md`.
- Validation round per `docs/09-human-validation-protocol.md`.
- First consented Darija recordings collected per
  `data/evaluation/speech/README.md`; first WER/CER + retrieval +
  grounding report produced.
- Corpus expansion at the same provenance bar.

### Later milestones

- End-user authentication, deployment.
