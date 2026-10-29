# LocaleVoice — App Flow (Milestone 1)

This document describes the intended end-to-end flow. Milestone 1 implements
only the two hosted-API provider modules and their smoke scripts; the flow
below is the system of record that later milestones build toward.

## 1. Flow overview

```
[1 Record / upload] -> [2 Transcribe] -> [3 Review + edit transcript]
  -> [4 Retrieve evidence] -> [5 Generate answer] -> [6 Display answer + sources]
```

Every stage can fail; every failure is reported honestly with a retry path
(see section 3). Milestone 1 scope covers the API primitives behind stages 2
and 5 only.

## 2. Stage definitions

### Stage 1 — Record or upload a short question

- Input: a short spoken question (tens of seconds), recorded in-app or
  uploaded as a WAV file.
- Output: an audio artifact for stage 2.
- Milestone 1: no UI. The transcription smoke test takes a user-provided WAV
  path on the command line.

### Stage 2 — Transcribe the actual recording

- The actual recording is sent to Meta Muse Voice Transcribe
  (`POST https://api.meta.ai/v1/asr/transcribe`, multipart: `request` JSON
  part plus audio file part).
- The `request` part carries the model identifier, `PUSH_TO_TALK` mode, WAV
  encoding, and an optional Arabic language bias (a hint, not a guarantee of
  Darija support — see `docs/02-technical-requirements.md`).
- Output: transcript text, or a reported failure.
- Milestone 1: implemented as `meta_asr.py` plus `scripts/transcribe_file.py`.

### Stage 3 — Review and edit the transcript

- The user sees the transcript and can correct it before retrieval runs.
- Rationale: ASR output — especially for Darija, whose support is
  unvalidated — must never flow silently into advice.
- Milestone 1: not implemented (no UI). Documented here as a required gate
  for Milestone 3.

### Stage 4 — Retrieve relevant evidence

- The reviewed transcript queries a curated agricultural reference corpus.
- Output: ranked evidence passages with source identifiers, or an explicit
  "no evidence" outcome.
- Milestone 1: not implemented. Designed in `docs/05-data-and-api.md`,
  built in Milestone 2.

### Stage 5 — Generate an answer

- A Meta-hosted language model (Meta Model API via the OpenAI SDK at
  `https://api.meta.ai/v1`) generates an answer grounded in the retrieved
  evidence.
- Milestone 1: only the provider primitive and its smoke test
  (`meta_chat.py` plus `scripts/verify_meta_chat.py`) exist. No advice
  pipeline, no grounding logic.

### Stage 6 — Display the answer and supporting sources

- The user sees the answer together with the sources it relies on.
- Milestone 1: not implemented (no UI).

## 3. Failure states and retries

| Failure                          | Behavior                                            |
| -------------------------------- | --------------------------------------------------- |
| Missing API key                  | Block before any call; name the variable to set.    |
| Invalid audio (missing, non-WAV) | Reject before any network call with a clear reason. |
| Network / API error              | Plain-language message, safe diagnostics, retry.    |
| Empty model response             | Reported as failure, never as an answer.            |
| Unsupported question (later)     | Say so explicitly; do not fabricate guidance.       |
| Missing evidence (later)         | Say so explicitly; offer to rephrase or retry.      |

Retries re-run the failed stage only; a corrected transcript is never
silently re-transcribed.

## 4. Assumptions

- Short questions; long recordings are out of scope for the MVP.
- Connectivity is available at request time; offline use is out of scope.
- Darija transcription quality is unvalidated until real recordings are
  tested; the stage-3 review gate exists partly for this reason.

## 5. Acceptance criteria (Milestone 1)

- This flow agrees with the other five documents.
- The stage-2 and stage-5 primitives named here exist and are smoke-tested
  against the real hosted APIs.

## 6. Non-goals

No UI, retrieval, advice generation, end-user auth, or deployment in this
milestone (see `docs/01-product-requirements.md`).

## 7. Privacy considerations

- Recordings and transcripts are user data; see `docs/05-data-and-api.md`.
- Review-before-retrieval keeps unvalidated ASR output away from advice.

## 8. Next milestones

- Milestone 2: stages 4–5 wired over reviewed transcripts (CLI-driven).
- Milestone 3: full six-stage UI. Details in
  `docs/06-implementation-plan.md`.
