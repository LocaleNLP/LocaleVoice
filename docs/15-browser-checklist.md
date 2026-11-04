# Browser Verification Checklist (Milestones 4A–5.1)

Run on your machine with a real browser. Automated UI flows in
`tests/test_app.py` are headless and are NOT browser verification.

Setup: `pip install -r requirements.txt`, a valid `MODEL_API_KEY` in
`.env`, then `streamlit run app.py` and open the printed local URL
(usually http://localhost:8501). Steps 2, 3, and 11 make live Meta
API calls (key required, requests billable); all other steps are
offline-safe.

Status: **all 15 steps BLOCKED in the development sandbox**
(`streamlit run` fails with `PermissionError: [Errno 1]` on socket
bind; no browser or automation binary available). No step has been
run in a real browser yet. Result vocabulary: PASS / FAIL / BLOCKED
/ NOT TESTED.

## Step 1 — App loads

- Preconditions: app installed; server started.
- Action: open the local URL in a desktop browser.
- Expected: title shows, no errors, Ask screen with upload,
  record, and typed-question options.
- Result: NOT TESTED. Notes: _

## Step 2 — WAV upload and transcription

- Preconditions: step 1 PASS; a short real WAV recording ready.
- Action: upload the WAV; confirm the player appears and the audio
  plays back; submit for transcription.
- Expected: playback works; app reaches the Review screen with the
  real ASR transcript. (Live ASR call.)
- Result: NOT TESTED. Notes: _

## Step 3 — Browser recording

- Preconditions: step 1 PASS; microphone permitted.
- Action: record in the browser; play back; submit for
  transcription. Then try a non-WAV file.
- Expected: recording transcribes (bytes validated as WAV); the
  non-WAV file gets an honest re-upload message. (Live ASR call.)
- Result: NOT TESTED. Notes: _

## Step 4 — Transcript review and correction

- Preconditions: step 2 or 3 reached Review (or typed fallback).
- Action: check recognized text is read-only and corrected text is
  editable; edit, then Confirm. Then try confirming empty text.
- Expected: Confirm reaches Answer (or the One-question screen when
  context is missing); empty confirm shows a clear message and
  stays on Review.
- Result: NOT TESTED. Notes: _

## Step 5 — Typed fallback

- Preconditions: step 1 PASS.
- Action: type a question instead of using audio; continue and
  confirm.
- Expected: reaches Answer or Clarify as appropriate for the text.
- Result: NOT TESTED. Notes: _

## Step 6 — Source expansion

- Preconditions: an evidence-backed answer on screen (e.g. after
  step 11).
- Action: expand each evidence expander.
- Expected: each shows ID, title, publisher, score, matched terms,
  and source URL.
- Result: NOT TESTED. Notes: _

## Step 7 — Off-corpus question

- Preconditions: step 1 PASS.
- Action: ask something off-corpus (e.g. capital of Morocco).
- Expected: warning shown, no answer fabricated, no model call.
  (No live call.)
- Result: NOT TESTED. Notes: _

## Step 8 — Failures and retry

- Preconditions: step 1 PASS.
- Action: try invalid content, an oversize file, and (optionally)
  an invalid key.
- Expected: each shows a clear message with Retry / Start-over;
  retry and restart both work.
- Result: NOT TESTED. Notes: _

## Step 9 — Narrow/mobile layout

- Preconditions: none beyond step 1.
- Action: repeat steps 2–7 in a narrow/mobile-sized window.
- Expected: layout usable; no step blocked by screen size.
- Result: NOT TESTED. Notes: _

## Step 10 — Clarification turn

- Preconditions: step 1 PASS.
- Action: type `شحال كتسقي الزرع فالسيمانة؟` and confirm.
- Expected: the One-question screen shows the original question
  plus the conversation so far. (No live call.)
- Result: NOT TESTED. Notes: _

## Step 11 — Reply with context (live answer)

- Preconditions: step 10 reached the One-question screen.
- Action: reply `القمح`.
- Expected: an evidence-backed answer with the wheat source
  appears. (Live chat call.)
- Result: NOT TESTED. Notes: _

## Step 12 — Reply without evidence, then restart

- Preconditions: step 1 PASS.
- Action: restart; ask about rainfall; reply with a location;
  reply a second time; then Finish and Start over.
- Expected: the still-missing note shows, the conversation stays
  open, both responses accumulate, and restart is clean.
  (No live call.)
- Result: NOT TESTED. Notes: _

## Step 13 — Conversation trace

- Preconditions: an answered or clarified conversation on screen.
- Action: open the Conversation expander on the Answer screen.
- Expected: every turn shown in order.
- Result: NOT TESTED. Notes: _

## Step 14 — Developer diagnostics

- Preconditions: an answer result on screen.
- Action: open the Developer diagnostics expander.
- Expected: retrieval/evidence trace shown (intent, terms, scores,
  selected evidence, rejection reasons, model invocation, citation
  check) with no secrets.
- Result: NOT TESTED. Notes: _

## Step 15 — Social intents

- Preconditions: step 1 PASS.
- Action: type `السلام عليكم`, then `شكرا بزاف`.
- Expected: each gets an instant natural reply with no sources
  and no model call. (No live call.)
- Result: NOT TESTED. Notes: _
