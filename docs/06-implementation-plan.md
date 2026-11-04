# LocaleVoice — Implementation Plan (Milestone 6D)

## 0k. Milestone 6D work items — live evaluation + relevance (done)

1. Live evaluator (`scripts/evaluate_live_answers.py` +
   `evaluation/live.py`, 15 cases): dry-run + live modes, full
   per-case records incl. traces. 10 evaluator unit tests (mocked).
2. Live run 2026-11-04 (`muse-spark-1.3`): 14 calls, 0 errors,
   15/15 outcomes, 14/14 syntax+containment, scoping verified
   (incl. dosage refusal). Report under data/evaluation/live/.
3. Relevance audit: English over-retrieval via shared livestock
   terms documented; `can/used/use/using` stopwords added with
   zero regressions; thresholds/embeddings rejected with evidence.
   Darija retrieval exact; alfalfa exclusion verified live.
4. Hygiene fix: Latin detection scoped to Arabic-script answers;
   French-elision false positive fixed (L15 re-checked clean).
5. Reviewer package: docs/20 seeded with verbatim live Darija
   answers (R1/R2, both PENDING); docs/09 procedure added.
6. Regression: 346 passed; 7/7 and 20/20 hold. No human, browser,
   or ASR validation claimed. No commit/push.

## 0j. Milestone 6C work items — answer quality + grounding (done)

1. Diagnosis: malformed citations were invisible to validation
   (`olive-cake]` passed containment); no language-consistency
   rules; tangential retrieval + weak prompt allowed topic mixing.
2. Prompt 8→12 rules: evidence-only, no invented regional facts,
   exact citations, answer-only-the-question, multi-part scoping,
   fixed answer structure, one-language rule.
3. Validation: malformed-citation detection (`syntax_ok`) with UI
   warning; hygiene flags (Latin fragments, repeated sentences)
   in trace; limits documented (containment ≠ truth, no semantic
   verification, no automated Darija proof).
4. Suites: `test_answer_hygiene` (7) + `test_answer_quality` A–L
   (13, mocked); problem-answer fixture reconstructed from
   symptoms (no screenshot provided).
5. Live: multi-topic Darija question structured correctly, soil/
   climate named uncovered, trace clean — one sample, not proof.
6. Regression: 335 passed (21 new); 7/7 and 20/20 hold. Human
   Darija approval still pending. No commit/push.

## 0i. Milestone 6B work items — safety audit + validation readiness (done)

1. Audit found 7 issues; all fixed: temp-dir leak on conversion
   failure, unmapped ffmpeg timeout, unbounded conversion work,
   missing truncation check, misdiagnosed normalization errors in
   the UI, stale retry op-tag, eligibility outside the retrieval
   layer. Bonus find: `wave` raises bare RuntimeError on garbage.
2. Eligibility moved into `retrieve(eligible_only=True)`, used by
   the pipeline, both eval runners, and the speech-eval script;
   pending docs no longer consume rank slots. 5 new tests
   (ineligible citation flagged, clarification cannot bypass).
   Statuses: 3 verified, alfalfa pending (not promoted).
3. Speech matrix + TTS readiness protocol: `docs/17` (9 scenarios,
   all PENDING, 0 recordings; 5-gate vendor verification, none
   selected, null backend stays).
4. UI review: all 8 points verified (grounded-only Listen, no
   autoplay, cached replays, cleared state, scoped errors).
5. Regression: 314 passed (12 new); 7/7 and 20/20 evals hold;
   speech 0 samples. No live/browser/human validation claimed.
   No commit/push.

## 0h. Milestone 6A work items — voice responses + upload reliability (done)

1. Diagnosis: uploads failed because validation checked 12 magic
   bytes only; real-world stereo 44.1/48 kHz WAVs reached Meta,
   which 400s anything but mono s16le 16/24 kHz (reproduced live).
   Mic worked because Streamlit records conforming 16 kHz WAV.
2. Normalization (`audio/normalize.py`): magic-byte sniffing, full
   WAV header parse, FFmpeg conversion to mono s16le 24 kHz;
   WAV/MP3/M4A/WebM accepted; 10 MiB / 120 s limits; safe temp
   files; conforming input passes through byte-identical.
3. ASR errors categorized (9 categories + config) with user
   guidance and safe diagnostics (formats, sizes, status, session
   id); stale failure state fixed (cleared at op start/success,
   op-tagged) with 6 AppTest regressions.
4. TTS: vendor-neutral interface + null backend (no provider
   selected — none verified for Darija; comparison in docs/16).
   Answer screen gained an opt-in Listen control (grounded answers
   only, session-scoped cache, failures keep the text).
5. Regression: 302 passed (48 new); 7/7 and 20/20 evals hold;
   live loop-closure verified (former 400 now 200). No browser
   run, no TTS vendor, no human validation. No commit/push.

## 0g. Milestone 5.1 work items — pre-validation safety fixes (done)

1. Review-status enforcement: only `verified-excerpt` docs are
   eligible as answer evidence (`is_answer_eligible`, fail closed);
   pending-review/rejected/archived matches are excluded in
   `answer_question` and the eval runner, stay visible in
   diagnostics with explicit exclusion reasons. 8 new tests; alfalfa
   entry kept, now abstains. Fixtures updated (m2-eval-1.2.0,
   m4e-eval-1.1.0): alfalfa items expect abstention, cowpea/alfalfa
   multi replaced by cowpea/wheat.
2. Consent script (`docs/12`): seven points made explicit; Darija
   version added, HUMAN REVIEW PENDING; no legal claims. Withdrawal
   and deletion procedure documented step by step (manual, nothing
   automatic); reports carry no transcript content.
3. Browser checklist restructured into
   `docs/15-browser-checklist.md` (preconditions/action/expected/
   result/notes × 15); all NOT TESTED here (sandbox BLOCKED).
4. Regression: 254 passed; 7/7 and 20/20 evals hold; speech 0
   samples; no browser/human validation claimed. No commit/push.

## 0f. Milestone 5 work items — human validation readiness (done)

1. Darija review (`docs/08`): all 15 user-facing messages verified
   verbatim against code; Context + Final-status fields added; mixed
   generic-abstention message added; Darija-vs-MSA review guidance.
   All HUMAN REVIEW PENDING, none approved, no LLM rewrites.
2. Speech workflow: consent gap closed — non-granted samples are
   never scored, retrieved, or transcribed even if transcripts
   linger (2 new tests); optional `recording_context` /
   `recognition_notes` fields; WER/CER still null without a
   human-verified reference. Facilitator guide: `docs/12`.
3. Farmer tasks (`docs/13`): six observable tasks with a capture
   sheet; no coaching, no personal data.
4. Browser: checklist extended to 15 steps (social intents added);
   all BLOCKED, re-confirmed (socket bind denied, no browser).
5. Knowledge (`docs/14`): coverage map + unsupported topics;
   alfalfa stays pending-review; no new excerpts.
6. Regression: 246 passed (244 baseline + 2 consent tests); 7/7 and
   20/20 evals hold; speech eval 0 samples; live chat smoke OK.
   Participants: 0. Recordings: 0. WER/CER: null. No commit/push.

## 0e. Milestone 4E work items — end-to-end validation & knowledge audit (done)

1. Context slots: `extract_slot_values()` + `build_value_index()` split
   recognized corpus-backed values from unclassified terms (proper
   nouns never guessed); `animal` slot added; values/terms accumulate
   across turns and roll back on failed retries. 21 new tests.
2. Retrieval stemming: fused preposition+article prefixes (فال/بال/لل)
   now stem (فالطماطم→طماطم, للبقر→بقر) while genuine ف/ب-initial
   words (برسيم, فواكه) are preserved; season slot gains عام/سنه.
3. Intent: adversarial suite (34 tests); `Salam` + `شكرا بزاف`-style
   thanks fixed; thanks requires a head token (بزاف alone stays
   unclear); ag signals gain alfalfa/livestock/plural terms.
4. Knowledge audit (`docs/10-knowledge-audit-4e.md`): all 4 excerpts
   sentence-verbatim on live Feedipedia pages, in order; 14/14
   keywords, publishers, and update stamps verified. Alfalfa stays
   pending-review. Manifest date wording corrected.
5. Benchmark (`data/evaluation/questions_4e.json`, 20 items):
   20/20 recall+gating offline; 5/5 clarification categories; 10/10
   model-call discipline; 1 extra lexical match noted (alfalfa via
   "cattle"). Pinned by `tests/test_eval_4e.py`. See
   `docs/11-evaluation-4e.md`.
6. Live: chat smoke OK; grounded wheat answer with contained
   citations; greeting/unsupported make no model call; ASR endpoint
   reachable (tone probe, no speech → honest empty result). No real
   Darija recording: speech quality still unmeasured.
7. Browser: still BLOCKED (socket bind denied, no browser);
   checklist extended to 14 steps (diagnostics) and re-confirmed.
8. Tests: 244 passed (61 new: 21 slots, 35 intent, 5 eval-set);
   base eval still 7/7. No commit/push.

## 0d. Milestone 4D work items — retrieval & conversation intelligence (done)

1. Intent layer (`pipeline/intent.py`): deterministic greeting/thanks/
   goodbye/agricultural/unsupported/unclear classification; social
   intents resolve instantly with no model call; unsupported-domain
   questions get a distinct abstention. Darija wording PENDING review.
2. Corpus migrated to the structured 4D schema (id/title/source_name/
   source_url/category/crop_or_species/excerpt/keywords/language/
   date_accessed/review_status); 4th genuine excerpt added (alfalfa,
   pending second-person review); curation process documented in
   `data/knowledge/README.md`. Internal evidence contract unchanged.
3. Retrieval: hamza folding, opt-in IDF weighting (count baseline
   byte-identical), `--min-score` CLI flag, documented thresholds.
4. Evidence trace on every result (`pipeline/trace.py`) + post-
   generation citation containment check (reported, never claimed as
   factual verification); UI diagnostics expander, unsupported banner,
   citation caption; prompt rule against inventing sources.
5. Clarification context-slot tracking (location/crop/season/soil/
   problem) with recorded, never-repeated follow-ups.
6. Tests: 183 passed (44 new); offline eval 7/7 with new alfalfa
   fixture; live chat smoke + grounded Darija answer re-verified.
   No browser run; no Darija audio; no commit/push.

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

### Milestone 4D — Retrieval & conversation intelligence (done)

See section 0d.

### Milestone 4E — End-to-end validation & knowledge audit (done)

See section 0e.

### Milestone 5 — Human validation readiness (done)

See section 0f. Preparation only: no reviewer, round, or recording
was completed in this milestone.

### Milestone 6 — First human validation round (single next milestone)

- A person runs the browser checklist (`docs/15-browser-checklist.md`,
  desktop + mobile), including the multi-turn conversation steps, and
  records PASS/FAIL.
- Darija speaker completes `docs/08-darija-language-review.md`.
- Validation round per `docs/09-human-validation-protocol.md`.
- First consented Darija recordings collected per
  `data/evaluation/speech/README.md`; first WER/CER + retrieval +
  grounding report produced.
- Corpus expansion at the same provenance bar.

### Later milestones

- End-user authentication, deployment.
