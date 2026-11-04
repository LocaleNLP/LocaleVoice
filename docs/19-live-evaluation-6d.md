# Live Model Evaluation (Milestone 6D)

## What was executed

- New evaluator `scripts/evaluate_live_answers.py` (+
  `src/localevoice/evaluation/live.py`, 15 versioned cases in
  `data/evaluation/live_cases_6d.json`). Dry-run lists cases with
  zero provider calls; live mode calls the configured Meta chat
  model at most once per answerable case through the real
  `answer_question` pipeline (no duplicated logic).
- Live run 2026-11-04, `muse-spark-1.3`: 15 cases, 14 model calls
  (~19–75 s each), 0 errors. Report:
  `data/evaluation/live/live_6d_20261104-200340.json`.
- Mocked: full unit suite (346 tests), offline evals, evaluator
  unit tests. Live: 14 chat calls above. No live ASR, no browser
  run, no human review in this milestone.

## Live results per axis (no aggregate score)

- Outcome match: 15/15 (14 answers incl. 6 scoped, 1 abstention).
- Citation syntax: 14/14 `syntax_ok`, 0 malformed.
- Citation containment: 14/14, 0 unknown IDs.
- Hygiene: 13/14 clean at runtime; the L15 flag (`d'olive`) was a
  false positive from French elision, fixed after the run
  (elision-aware allowlist) — re-checked clean on both Darija
  answers. The saved report preserves the original flag.
- Evidence relevance: the model stayed scoped in every case
  (L04 cited wheat only from 3 supplied; L05 used olive+wheat for
  a genuine comparison and ignored cowpea; L07/L08/L09 refused
  soil/climate/dosage with specialist referrals). Relevance
  judgments below are the operator's reading, not a metric.
- Claim-level factual support: NOT MEASURED (no entailment
  method; containment is not accuracy).
- Human-rated Darija naturalness: NOT MEASURED (0 reviewers;
  sheet ready at `docs/20-darija-answer-review-6d.md`).

## Retrieval relevance audit (Phase 3)

Method: per-case raw ranking vs subject-relevant set (see case
file). Findings:

- English questions over-retrieve via shared livestock vocabulary
  ("feed", "grain", "cattle", "ruminants", "sheep", "hay") at
  score 1–2: 7 of 15 cases retrieve a tangential doc (e.g. L12
  olive via "ruminants", L10 olive+cowpea alongside wheat).
- Darija questions retrieve exactly (L14, L15, L06 abstains
  cleanly) — the primary user path is precise.
- Ineligible (alfalfa) matches appear in raw ranking (L10, L12,
  L13) but never in supplied evidence — exclusion verified live.
- Fix landed: `can/used/use/using` added to stopwords (L03/L05
  noise reduced). Suite + both offline evals green after the
  change (335→346 with new tests).
- Rejected with evidence: `min_score=2` would abstain the core
  Darija wheat case (score 1) — unacceptable; score-gap and
  category filters are inconsistent on ties and add unjustified
  complexity; embeddings/vector DB not warranted while prompt
  rule 4 (answer-only-the-question) demonstrably holds the line
  live. Residual over-retrieval is documented, not hidden.

## Failures and blockers

- Failures in live behavior: none observed across 15 cases.
- Tooling false positive: L15 `d'olive` hygiene flag (fixed).
- Remaining blockers for farmer readiness: (1) Darija
  naturalness unreviewed (docs/08 + docs/20 pending); (2) no real
  speech validation (0 recordings, WER/CER null); (3) no browser
  run (sandbox BLOCKED); (4) 3-doc eligible coverage — most real
  questions will abstain by design.
