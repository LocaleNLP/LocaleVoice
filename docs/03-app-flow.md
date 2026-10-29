# LocaleVoice — App Flow (Milestone 2)

Milestone 2 implements stages 2, 4, and 5 as tested CLI-driven modules; the
full six-stage voice UX still awaits the Milestone 3 UI. This document is
the system of record for the flow.

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
- Status: no UI yet. `scripts/transcribe_file.py` takes a user-provided WAV
  path; `scripts/answer_question.py` accepts typed text directly.

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
- Status: not implemented (needs the Milestone 3 UI). The CLI accepts
  already-reviewed text, which plays the role of a reviewed transcript.

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
- Status: CLI display only (answer, evidence list with scores,
  insufficient-evidence flag). Full UX in Milestone 3.

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
- Corpus coverage is narrow (3 excerpts); most questions take the
  insufficient-evidence path by design.

## 5. Acceptance criteria (Milestone 2)

- This flow agrees with the other five documents.
- Stages 2, 4, and 5 exist as tested modules with live-verified behavior.

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
