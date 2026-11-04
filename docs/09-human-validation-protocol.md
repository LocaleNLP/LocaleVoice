# Human Validation Protocol — First Controlled Round (Milestone 4C)

Small-group validation with Moroccan Darija speakers and representative
farmers. Goal: separate **software correctness** (does the flow work),
**language quality** (is the Darija understood), and **agricultural
usefulness** (is the answer or abstention appropriate). No round has
been run yet.

## Setup

- Facilitator runs `streamlit run app.py` locally with a valid
  `MODEL_API_KEY`; participant uses the browser (desktop or phone).
- Explain first: this is a prototype with 3 reference excerpts, so most
  questions will end in clarification or honest abstention. That is the
  expected behavior under test, not a failure.
- Consent: spoken questions may be transcribed by the hosted ASR
  service. Do not record sessions without explicit consent; see
  `data/evaluation/speech/README.md` if collecting samples.

## Scenarios (one per participant, ~5 minutes each)

1. **Crop identification** — "Ask what cowpea (niébé / اللوبياء) is and
   whether it suits livestock." Expect: grounded answer with the
   cowpea source.
2. **Feeding and livestock** — "Ask whether wheat is good for cattle,
   in your own words." Expect: grounded answer with the wheat source,
   or a clarification if wording misses.
3. **Irrigation** — "Ask how much to irrigate crops per week." Expect:
   the irrigation clarification asking which crop; after answering
   `القمح`, a wheat-grounded answer; after anything else, an honest
   still-missing note.
4. **Soil conditions** — "Ask about the state of the land this year."
   Expect: the soil clarification (soil test / observations).
5. **Seasonal questions** — "Ask whether rainfall was enough for the
   season." Expect: the rainfall clarification (location + season),
   then abstention with the still-missing note.
6. **Outside the knowledge base** — "Ask anything the 3 excerpts
   cannot cover (e.g. the capital of Morocco)." Expect: generic
   abstention, no fabricated answer.

## Capture per scenario

| # | Question asked |
|---|----------------|
| 1 | Did the participant understand what the system asked them? (y/n + note) |
| 2 | Could they provide a useful clarification response? (y/n + note) |
| 3 | Did the system retrieve relevant evidence? (doc IDs or none) |
| 4 | Was the final answer/abstention understandable? (y/n + note) |
| 5 | Was abstention appropriate, if it abstained? (y/n + note) |
| 6 | Would they trust this response? (y/n + why) |

## Scoring (separate axes, do not blend)

- **Software correctness**: stages advance, trace is complete, no
  crashes, no duplicated turns, errors are honest. Target: 100% of
  scripted flows complete.
- **Language quality**: participant understands prompts and answers
  without facilitator help. Record verbatim confusion points for
  `docs/08-darija-language-review.md`.
- **Agricultural usefulness**: grounded answers match the cited
  excerpt; abstentions correctly refuse uncovered topics. Any
  unsupported claim is a blocking defect regardless of the other axes.

## Stop rules

Stop the round and fix before continuing if: any fabricated citation
or agricultural claim appears; a participant is misled into a wrong
farming action; personal data or audio leaves the documented paths.
