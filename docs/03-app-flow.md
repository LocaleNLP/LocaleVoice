# LocaleVoice — App Flow (Milestone 3)

Milestone 3 wires stages 1–6 into a working Streamlit app over the tested
Milestone 2 modules. This document is the system of record for the flow.

## 1. Flow overview

```
[1 Record / upload] -> [2 Transcribe] -> [3 Review + edit transcript]
  -> [4 Retrieve evidence] -> [5 Generate answer] -> [6 Display answer + sources]
```

Every stage can fail; every failure is reported honestly with a retry path
(see section 3).

## 2. Stage definitions and implementation status

### Stage 1 — Record or upload a short question

- Input: a short spoken question (tens of seconds), recorded in-app or
  uploaded as a WAV file.
- Status: implemented in the app (WAV upload, `st.audio_input`
  recording with RIFF validation, typed fallback).

### Stage 2 — Transcribe the actual recording

- The actual recording is sent to Meta Muse Voice Transcribe
  (`POST https://api.meta.ai/v1/asr/transcribe`, multipart: `request` JSON
  part plus `audio` file part).
- The `request` part carries the model identifier, `PUSH_TO_TALK` mode,
  `audioEncoding` (`WAV`), and an optional Arabic language bias (a hint,
  not a guarantee of Darija support — see
  `docs/02-technical-requirements.md`).
- Status: implemented (`meta_asr.py`); request shape validated live.
  Transcription of real Darija speech is still unvalidated (no consented
  recording tested yet).

### Stage 3 — Review and edit the transcript

- The user sees the transcript and can correct it before retrieval runs.
- Rationale: ASR output — especially for Darija, whose support is
  unvalidated — must never flow silently into advice.
- Status: implemented in the app as a mandatory gate — recognized
  transcript shown read-only, corrected version edited and confirmed
  before anything is answered. Confirmation starts a `Conversation`
  (Milestone 4B): direct answers and generic abstentions go to stage 6,
  while categorized no-evidence questions go to a clarify turn first.

### Stage 4 — Retrieve relevant evidence

- The reviewed transcript queries the versioned corpus
  (`data/knowledge/`); deterministic lexical baseline returns ranked
  passages with document IDs and scores, or an empty set.
- Status: implemented (`knowledge/`), evaluated offline 6/6 on fixtures.

### Stage 5 — Generate an answer

- With evidence: the Meta-hosted chat model generates a concise answer
  grounded strictly in the supplied passages, with `[document_id]`
  citations. Without evidence: a transparent insufficient-evidence
  response, no model call, no guessing.
- Status: implemented (`pipeline/`); live run verified with citations
  contained in supplied IDs.

### Stage 6 — Display the answer and supporting sources

- The user sees the answer together with the sources it relies on.
- Status: implemented in the app (answer, source expanders with IDs and
  scores, insufficient-evidence banner, model/latency caption).

## 3. Failure states and retries

| Failure                          | Behavior                                            |
| -------------------------------- | --------------------------------------------------- |
| Missing API key                  | Block before any call; name the variable to set.    |
| Invalid audio (missing, non-WAV) | Reject before any network call with a clear reason. |
| Network / API error              | Plain-language message, safe diagnostics, retry.    |
| Empty model response             | Reported as failure, never as an answer.            |
| Empty corpus                     | CLI error before retrieval.                         |
| Unsupported question             | Insufficient-evidence response, no guessing.        |
| Missing evidence                 | Insufficient-evidence response; suggest rephrasing. |

Retries re-run the failed stage only; a corrected transcript is never
silently re-transcribed.

## 4. Assumptions

- Short questions; long recordings are out of scope for the MVP.
- Connectivity is available at request time; offline use is out of scope.
- Darija transcription quality is unvalidated until real recordings are
  tested; the stage-3 review gate exists partly for this reason.
- Corpus coverage is narrow (4 excerpts); most questions take the
  insufficient-evidence path by design.
- Intent routing (Milestone 4D): greetings/thanks/goodbye resolve
  instantly with no model call; clear out-of-domain questions get the
  unsupported-domain message; everything else flows to retrieval.
  UI states: greeting welcome, answer + sources, clarification,
  insufficient-evidence, unsupported-domain, failure.

## 5. Acceptance criteria (Milestone 3, validated through 4C)

- This flow agrees with the other documents.
- All six stages run in the app over tested modules; the audio path was
  verified live through the app's exact code path (in-browser check
  pending, see `docs/06-implementation-plan.md`).
- Milestone 4C status: conversation rollback integrity tested;
  browser checklist corrected to 13 steps, all BLOCKED here; Darija
  wording extracted for review (all PENDING); speech workflow ready
  with zero samples; no human round run yet.
- Milestone 5.1 status: browser checklist restructured with
  preconditions/actions/expected/results and extended to 15 steps
  (`docs/15-browser-checklist.md`), all BLOCKED here; review-status
  enforcement excludes pending-review excerpts from answers.

## 6. Non-goals

No UI, end-user auth, or deployment in this milestone (see
`docs/01-product-requirements.md`).

## 7. Privacy considerations

- Recordings and transcripts are user data; see `docs/05-data-and-api.md`.
- Review-before-retrieval keeps unvalidated ASR output away from advice.
- CLI run records exclude keys and unnecessary personal data.

## 8. Next milestones

- Milestone 3: full six-stage Streamlit UI. Details in
  `docs/06-implementation-plan.md`.
