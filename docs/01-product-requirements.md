# LocaleVoice — Product Requirements (Milestone 1)

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

## 4. Milestone 1 scope (this milestone)

- Six architecture documents (`docs/01`–`docs/06`) as the system of record.
- A small Meta chat provider module (Meta Model API via the OpenAI Python SDK).
- A real audio-file transcription provider (documented Meta ASR endpoint,
  multipart request format).
- `scripts/verify_meta_chat.py`: a real hosted chat smoke test.
- `scripts/transcribe_file.py PATH_TO_WAV`: a real transcription smoke test.
- Automated unit tests using mocks, so `python -m pytest -q` needs no network
  access and no paid API call.
- `README.md` with exact setup, test, and smoke-test commands.
- `.env.example` with no real secret; `.env` ignored by Git; audio fixtures
  kept out of Git.

## 5. Non-goals for Milestone 1

- No retrieval implementation and no agricultural reference corpus ingestion.
- No agricultural advice generation or answer-grounding pipeline.
- No Streamlit UI or other full user interface.
- No end-user authentication.
- No deployment, hosting, or CI/CD.

## 6. Assumptions

- Hosted inference only; no local model inference in any milestone.
- `MODEL_API_KEY` is provided via environment configuration and is valid for
  both the Meta Model API and the Meta ASR endpoint.
- `META_CHAT_MODEL` and `META_ASR_MODEL` are configurable model identifiers;
  their exact values must be confirmed against current Meta documentation.
- The documented Muse Voice Transcribe language list includes Arabic but does
  not explicitly list Moroccan Darija as a separate supported language. Arabic
  language bias is treated as a hint, not a guarantee of dialect support.
  Darija transcription quality is unvalidated until real Darija recordings are
  tested (see `docs/02-technical-requirements.md`).
- Short questions only in the MVP (tens of seconds of audio); long recordings
  are out of scope until a later milestone.

## 7. Acceptance criteria (Milestone 1)

- The six documents exist, agree with one another, and record explicit
  assumptions, acceptance criteria, non-goals, failure states, privacy
  considerations, and next milestones.
- `python -m pytest -q` runs with no live network calls and passes.
- The chat smoke test makes a real request to the Meta Model API and fails
  clearly (missing key, request failure, empty response) instead of silently.
- The transcription smoke test uploads an actual user-provided WAV recording
  and validates the real API response.
- Errors preserve useful status and diagnostic information without leaking API
  keys.
- No mocked response is presented as a real model result anywhere.
- No secrets and no unapproved audio fixtures are committed to Git.

## 8. Failure states (product behavior)

- Missing API key: block the request and tell the user which variable to set.
- API failure (network, auth, rate limit, server error): show a plain-language
  failure message with the safe diagnostic detail and offer a retry.
- Empty or unusable model response: report it as a failure, not as an answer.
- Unsupported question or missing evidence (later milestones): say so
  explicitly and do not fabricate guidance.
- Invalid audio input (missing file, non-WAV): reject before any network call
  with a clear reason.

## 9. Privacy considerations

- Voice recordings are personal data. Only user-provided recordings with
  explicit approval are used for testing, and actual audio fixtures stay out of
  Git unless explicitly approved for sharing with appropriate consent.
- API keys live in `.env` (Git-ignored), never in code, docs, logs, or error
  messages.
- Transcripts and answers derived from real recordings are handled as
  user data; see `docs/05-data-and-api.md`.

## 10. Next milestones

- Milestone 2: curated agricultural reference corpus plus retrieval and
  grounded answer generation over reviewed transcripts (still CLI-driven).
- Milestone 3: Streamlit voice-first UI (record/upload, transcript review,
  answer plus sources, honest failure states).
- Later: end-user authentication, evaluation on real Darija recordings,
  deployment.
