# Farmer Validation Tasks — First Round (Milestone 5)

Companion to `docs/09-human-validation-protocol.md` (scenarios and
scoring axes) and `docs/12-audio-collection-guide.md` (consent and
recording). Six short tasks, one participant at a time, ~20 minutes
total. The facilitator operates the machine; the participant speaks
and decides.

Rules for the facilitator:

- Read each task prompt aloud exactly as written. Do not rephrase,
  suggest words, or hint at the expected answer.
- If the participant is stuck for more than a minute, mark the task
  incomplete and move on. Struggle is data.
- Collect no personal information: anonymous participant ID only
  (e.g. `P-01`), no names.
- Note the participant's own words wherever a judgment is asked.

## Task 1 — Start a conversation

Prompt: "Greet the assistant the way you would greet a person."

Observe: does the greeting reply feel natural? Record any wording
the participant would change (→ `docs/08-darija-language-review.md`).

## Task 2 — Ask an agricultural question by voice

Prompt: "Ask, in your own words, whether wheat is good feed for
cattle."

Observe: natural phrasing (record it verbatim if consented),
whether retrieval finds the wheat source, whether the final answer
is understandable. Do not correct their wording toward the corpus.

## Task 3 — Review and correct the transcript

Prompt: "Read what the system heard. Fix anything it got wrong,
then confirm."

Observe and count: number of transcript corrections (0, 1–2, 3+),
whether the participant could complete the correction unaided.

## Task 4 — Respond to a clarification request

Prompt: "Ask how much to water crops per week. Answer whatever the
system asks you next."

Observe: is the clarification question understood? Can they supply
the missing crop? Record the reply verbatim (if consented) and
whether the conversation completed or stalled.

## Task 5 — Inspect the source behind an answer

Prompt: "This answer came with sources. Open the source and tell me
whether you understand where the answer came from."

Observe: can they expand the source? Do they understand the
publisher/title/evidence link? Would they trust this response, and
why (their words)?

## Task 6 — Watch the system abstain

Prompt: "Ask something the system cannot know — for example whether
rainfall was enough this season, or anything outside farming."

Observe: does it abstain or clarify instead of guessing? Is the
abstention appropriate and understandable? Any fabricated claim is a
blocking defect: stop the round per `docs/09` stop rules.

## Capture sheet (one row per participant)

| Participant | T1 greeting natural? (y/n + note) | T2 question verbatim (if consented) | T2 evidence found? (doc IDs/none) | T2 answer understandable? | T3 corrections (count) | T3 unaided? | T4 clarification understood? | T4 reply verbatim (if consented) | T4 completed? | T5 source understood? | T5 trusted? (why) | T6 abstained? | T6 appropriate? | Usefulness (their words) | Failure points |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P-__ | | | | | | | | | | | | | | | |

## After the round

- Tally per-task completion; list every observed failure point.
- File Darija wording corrections in `docs/08`.
- File consented recordings per `docs/12`; run
  `python scripts/evaluate_speech.py [--transcribe]` and report
  WER/CER only where human-verified references exist.
- No round has been run yet: all cells above are empty by design.
