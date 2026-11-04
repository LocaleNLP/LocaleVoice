# LocaleVoice — Design Brief (Milestone 3)

Milestone 3 implements this brief as a Streamlit app (`app.py`). The
principles and screen contract below are unchanged from Milestones 1–2;
this revision adds the implemented visual system and build notes.

## 1. Design principles

- Voice first: the primary input is speech, not typing. Every screen must be
  usable by someone who speaks Darija but reads formal Arabic or English
  with difficulty.
- Trust through honesty: transcripts are shown before use, answers are shown
  with sources, and failures say what happened. Nothing mocked is ever shown
  as real.
- One question, one answer: a single linear flow (record → review → answer),
  no navigation maze.
- Forgiving: large touch targets, re-record and retry on every stage, and
  editable transcripts.

## 2. Intended screens (Milestone 3, for reference)

1. **Ask**: one prominent record button plus an upload-a-WAV alternative.
   Progress state while recording; clear stop/cancel.
2. **Review transcript**: the transcript in large text, editable, with
   re-record and confirm actions. A short note that automatic transcription
   can make mistakes is shown here.
3. **Answer**: the answer in plain language plus a visible source list
   (title/identifier per source). Actions: ask another question, retry.
4. **Failure**: plain-language explanation of what failed, what the user can
   do (retry, re-record, rephrase), and safe diagnostic detail kept
   unobtrusive.

## 3. Content and language guidance

- UI chrome in simple language; farming answers practical and jargon-free.
- Darija voice input is the goal, but transcription quality for Darija is
  currently unvalidated (see `docs/02-technical-requirements.md`); the UI
  must not promise dialect accuracy it cannot verify.
- Never present uncertain or missing information as fact; unsupported
  questions and missing evidence get explicit "I don't know" states.

## 4. Constraints from Milestones 1–2

The CLI vertical slice already defines the display contract the UI must
keep: answer text, evidence list with source IDs and scores,
insufficient-evidence flag, language/uncertainty note, and safe error
detail. Milestone 3 renders these four states (Ask, Review, Answer,
Failure) without changing their semantics.

- Provider error messages must already be plain-language-friendly: short
  summaries the UI can show, with safe detail available but not prominent.
- The transcript review gate is mandatory, not optional, precisely because
  ASR quality for Darija is unvalidated.
- No provider output may be faked for design purposes; design fixtures must
  be labeled as fixtures.

## 5. Implemented visual system (Milestone 3)

- Palette: obsidian `#14120F` (page background), deep umber `#1E1A14`
  (secondary surfaces), sand `#EDE4D3` (text), neon-lime `#C6FF3D`
  (primary accent), via `.streamlit/config.toml` (dark base).
- Minimal styling: one small CSS block (transcript/answer type scale,
  Arabic `dir="auto"` rendering, muted helper notes). No gradients,
  glow effects, or decorative widgets.
- Layout: centered single column (usable on desktop and mobile);
  two-button rows only. Loading via spinners; errors via inline
  failure blocks with Retry / Start-over actions.
- Screens map 1:1 to the contract: Ask (upload + in-browser record +
  typed fallback), Review (recognized vs corrected transcript),
  Answer (answer + source expanders + model/latency caption),
  Failure (plain message + collapsible technical detail).
- In-browser recording uses `st.audio_input`; bytes are RIFF-validated
  as WAV before transcription, and non-WAV input gets an honest
  re-upload message rather than a provider error.

## 5b. Assumptions

- Phone or laptop with microphone and modern browser; possible
  low-bandwidth connectivity, so keep audio uploads short and pages light.
- Streamlit is the planned UI framework (Milestone 3); this brief does not
  depend on framework-specific widgets.

## 6. Acceptance criteria (Milestone 3)

- This brief agrees with the other five documents.
- The app implements the four screens with the review gate mandatory and
  no mocked provider output shown as real.

## 7. Non-goals

- No end-user auth, deployment, or visual design system beyond section 5.
- No visual design system, branding, or styling beyond this brief.

## 8. Failure states

Covered by the Failure screen (section 2.4) and the shared failure table in
`docs/03-app-flow.md`: missing key, invalid audio, network/API errors, empty
responses, unsupported questions, and missing evidence each get an honest
state with a next action.

## 9. Privacy considerations

- Recording and upload controls must make clear that audio leaves the device
  for hosted transcription.
- Consent-gated handling of recordings carries through to the UI copy in
  Milestone 3.

## 10. Next milestones

- Milestone 3 (this milestone): Streamlit implementation of the four
  screens above — done.
- Later: end-user auth, Darija speech evaluation, corpus expansion,
  deployment.
