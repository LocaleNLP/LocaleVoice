# LocaleVoice — Implementation Plan (Milestone 2)

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

### Milestone 3 — Streamlit voice-first UI (the single next milestone)

- Record/upload, transcript review/edit gate, answer plus sources, honest
  failure states, per `docs/04-design-brief.md`.
- Wires the Milestone 2 pipeline behind the UI without changing its
  semantics; still no end-user auth, no deployment.

### Later milestones

- End-user authentication, real Darija recording evaluation (WER/CER only
  with real audio + references), corpus expansion at the same provenance
  bar, deployment.
