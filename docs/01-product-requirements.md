# LocaleVoice — Product Requirements (Milestone 2)

## 1. Product summary

LocaleVoice is a hackathon MVP for a voice-first agricultural assistant aimed at
Moroccan farmers. The user asks a farming question by voice in Moroccan Darija
and receives a practical written answer grounded in a curated agricultural
reference corpus, with the supporting sources shown.

## 2. Target user

A Moroccan farmer who wants practical agricultural guidance without needing to
interact entirely in formal written Arabic or English. Assume:

- The user is comfortable speaking Darija but may not read or write fluently in
  formal Arabic or English.
- The user has a phone or laptop with a microphone and a modern browser.
- The user may have intermittent or low-bandwidth connectivity.

## 3. Intended end-to-end flow

1. The user records or uploads a short spoken question.
2. The system transcribes the actual recording using Meta-hosted speech
   recognition (Meta Muse Voice Transcribe).
3. The user reviews and edits the transcript before anything else runs.
4. The system retrieves relevant evidence from a curated agricultural reference
   corpus.
5. The system generates an answer using a Meta-hosted language model
   (Meta Model API).
6. The answer is displayed together with the supporting sources.
7. Unsupported questions, missing evidence, API failures, and retries are
   handled honestly: the system says what happened and what the user can do,
   and never presents a mocked or guessed result as a real model output.

## 4. Milestone 2 scope (this milestone, implemented)

- Versioned agricultural corpus (`data/knowledge/`): 3 verified Feedipedia
  excerpts (cowpea, olive cake, wheat grain) with full provenance, plus a
  manifest. Narrow coverage by design.
- Deterministic lexical retrieval baseline over the corpus, with documented
  search-only normalization for Arabic script and French terms.
- Grounded answer pipeline: retrieved evidence is the only permitted factual
  basis; insufficient-evidence questions get a transparent no-guess response
  with no model call.
- `scripts/answer_question.py`: CLI vertical slice (question in, sourced
  answer out, optional run-record saving).
- `scripts/evaluate_pipeline.py`: offline and live evaluation over versioned
  synthetic fixtures (retrieval recall, gating, citation containment,
  latency, model ID).
- `scripts/validate_corpus.py`: corpus schema validation.
- 44 new unit tests (65 total), all offline with mocked chat.

## 5. Non-goals for Milestone 2

- No Streamlit UI or other full user interface (transcript review gate still
  pending a UI).
- No end-user authentication.
- No deployment, hosting, or CI/CD.
- No embedding/vector retrieval (lexical baseline only, by design).
- No WER/CER or language-quality claims: fixtures are synthetic and
  manually authored, explicitly not real farmer data. Real Darija ASR
  quality is still pending until actual consented speech is transcribed
  and reviewed.

## 6. Assumptions

- Hosted inference only; no local model inference in any milestone.
- `MODEL_API_KEY` is provided via environment configuration and is valid for
  both the Meta Model API and the Meta ASR endpoint.
- `META_CHAT_MODEL=muse-spark-1.3` and `META_ASR_MODEL=muse-voice-transcribe-1.0`
  were confirmed live via the API model list and successful requests.
- The documented Muse Voice Transcribe language list includes Arabic but does
  not explicitly list Moroccan Darija as a separate supported language. Arabic
  language bias is treated as a hint, not a guarantee of dialect support.
- Lexical retrieval matches shared vocabulary only; it is not Darija
  semantic understanding and must never be described as such.
- Short questions only in the MVP (tens of seconds of audio).

## 7. Acceptance criteria (Milestone 2)

- `python -m pytest -q` passes with no network access and no paid API call.
- `scripts/validate_corpus.py` reports the corpus valid.
- Offline evaluation passes on all fixtures (recall + gating).
- A real Meta-generated answer was produced with citations contained in the
  supplied source IDs (verified in the live evaluation run).
- A no-evidence question returns the transparent insufficient-evidence
  response with no model call.
- Errors preserve useful status and diagnostic information without leaking API
  keys.
- No mocked response is presented as a real model result anywhere.
- No secrets and no unapproved audio fixtures are committed to Git.

## 8. Failure states (product behavior)

- Missing API key: block the request and tell the user which variable to set.
- API failure (network, auth, rate limit, server error): show a plain-language
  failure message with the safe diagnostic detail and offer a retry.
- Empty or unusable model response: report it as a failure, not as an answer.
- Empty corpus: CLI exits with an error before retrieval.
- Unsupported question or missing evidence: explicit insufficient-evidence
  response; no fabricated guidance, no invented sources.
- Invalid audio input (missing file, non-WAV): reject before any network call
  with a clear reason.

## 9. Privacy considerations

- Voice recordings are personal data. Only user-provided recordings with
  explicit approval are used for testing, and actual audio fixtures stay out of
  Git unless explicitly approved for sharing with appropriate consent.
- API keys live in `.env` (Git-ignored), never in code, docs, logs, run
  records, evaluation reports, or error messages.
- Run records and evaluation reports store questions, evidence IDs, and
  model outputs only; no keys or unnecessary personal data.
- Corpus excerpts are short attributed passages stored for prototype
  evaluation; check source terms before redistribution.

## 10. Next milestones

- Milestone 3: Streamlit voice-first UI (record/upload, transcript review,
  answer plus sources, honest failure states).
- Later: end-user authentication, evaluation on real Darija recordings,
  corpus expansion, deployment.
