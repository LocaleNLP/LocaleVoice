# LocaleVoice — 20-Question Benchmark Results (Milestone 4E, Phase 4–5)

Set: `data/evaluation/questions_4e.json` (`m4e-eval-1.0.0`, 20 synthetic
items). Base set `questions.json` (7 items) kept separately: still
7/7 recall+gating. Fixtures are synthetic, not farmer data; no claim
about real-world Darija quality follows from these numbers.

## Offline results (2026-11-04)

Command: `python scripts/evaluate_pipeline.py --fixtures
data/evaluation/questions_4e.json`

- Retrieval recall: **20/20** (every expected doc retrieved).
- Insufficient-evidence gating: **20/20** correct.
- Multi-doc items retrieving both docs: **2/2**.
- Clarification categories: **5/5** correct.
- Intent labels: **20/20** as documented.
- Model-call discipline (mocked): 8 called / 12 not called, as
  documented — social, unsupported, clarification, abstain, and
  pending-review paths never reach the model.

## Precision note (resolved by 5.1 enforcement)

In 4E, `4e-multi-wheat-olive-energy` retrieved wheat + olive
(expected) plus alfalfa via the genuine lexical match "cattle". Since
5.1, pending-review excerpts are excluded from evidence, so all 20
items now retrieve exactly the expected set. Any future precision
metric must still account for shared livestock vocabulary across
excerpts.

## Abstention correctness

All 12 no-evidence items (5 clarification, 2 unsupported, 1
treatment, 1 uncovered-agricultural, 1 social, 2 pending-review)
resolve without a model call and without fabricated content: 0
false-positive answers.

## Live provider results (2026-11-04, labeled)

1. Chat smoke (`verify_meta_chat.py`): OK, `muse-spark-1.3`,
   `LOCALEVOICE_SMOKE_OK`.
2. Supported question (live): Darija wheat answer grounded on
   `feedipedia-wheat-grain`, 25.9 s, citation containment
   `contained=True, invalid=[]`.
3. Greeting (live path): canned response, `model=None`,
   `model_called=False`.
4. Unsupported question (live path): domain message, `model=None`,
   `model_called=False`.
5. ASR endpoint: reachable — a 1 s 440 Hz tone probe returned a valid
   response shape (`sessionId`, empty transcript, no turns) and the
   CLI failed honestly on non-speech. Connectivity only: **no real
   Darija recording exists, so speech quality remains unmeasured** and
   WER/CER stay null.

## What the numbers do not prove

- The 20 fixtures were authored against the known 4-doc corpus; 20/20
  validates the pipeline wiring, not coverage of real farmer needs.
- Darija wording (intent responses, clarification, live answer) is
  HUMAN REVIEW PENDING (`docs/08`).
- No browser session has run (`docs/15-browser-checklist.md`, 15 steps, BLOCKED).
