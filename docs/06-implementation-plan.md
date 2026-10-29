# LocaleVoice — Implementation Plan (Milestone 1)

## 1. Milestone 1 work items (this milestone)

1. Inspect the existing repository and environment before changing files.
2. Write the six architecture documents (`docs/01`–`docs/06`), mutually
   consistent, with assumptions, acceptance criteria, non-goals, failure
   states, privacy considerations, and next milestones.
3. Create `.env.example` without a real secret; ensure `.env` is ignored by
   Git; keep audio fixtures out of Git.
4. Implement `src/localevoice/providers/meta_chat.py` (Meta Model API via
   the OpenAI SDK at `https://api.meta.ai/v1`).
5. Implement `src/localevoice/providers/meta_asr.py` (multipart `POST` to
   `https://api.meta.ai/v1/asr/transcribe`).
6. Create `scripts/verify_meta_chat.py` (real hosted chat smoke test).
7. Create `scripts/transcribe_file.py PATH_TO_WAV` (real transcription
   smoke test).
8. Add mocked unit tests so `python -m pytest -q` needs no network or paid
   API call.
9. Document exact setup, test, and smoke-test commands in `README.md`.
10. Run tests, attempt both smoke tests, and report evidence honestly.

## 2. Milestone 1 acceptance criteria

- `python -m pytest -q` passes with no live network calls.
- Chat smoke test makes a real request; transcription smoke test uploads a
  real user-provided recording; both report real outcomes (success or
  failure) without invention.
- Errors preserve status/diagnostics without leaking keys.
- No mocked response is presented as a real model result.
- Definition of done from the milestone brief is met and reported:
  files changed, commands, test results and exit codes, smoke-test
  outcomes, unresolved blockers, and the single next milestone.

## 3. Non-goals (Milestone 1)

No retrieval, agricultural advice generation, Streamlit UI, end-user
authentication, or deployment.

## 4. Assumptions

- Python 3.10+; hosted inference only.
- `MODEL_API_KEY`, `META_CHAT_MODEL`, `META_ASR_MODEL` from the environment.
- `python-dotenv`, `requests`, `pytest`, and the installed OpenAI SDK.
- Darija ASR support unvalidated; Arabic bias is a hint only.

## 5. Failure states

Per `docs/03-app-flow.md`: missing key, invalid audio, network/API errors,
and empty responses are all explicit, safe, nonzero-exit failures at the
CLI boundary.

## 6. Privacy considerations

Per `docs/05-data-and-api.md`: Git-ignored `.env` and sample audio,
consent-gated fixtures, redacted keys.

## 7. Next milestones

### Milestone 2 — Corpus, retrieval, and grounded answers (CLI-driven)

The single next milestone after Milestone 1:

- Curate a small agricultural reference corpus with stable source IDs.
- Implement transcript → retrieval → grounded-answer pipeline over the
  Milestone 1 providers (reviewed transcript text in, sourced answer out).
- CLI-driven evaluation with sample questions; still no UI, no end-user
  auth, no deployment.
- Begin real Darija recording tests to validate transcription quality.

### Milestone 3 — Streamlit voice-first UI

- Record/upload, transcript review/edit, answer plus sources, honest
  failure states, per `docs/04-design-brief.md`.

### Later milestones

- End-user authentication, broader Darija evaluation, deployment.
