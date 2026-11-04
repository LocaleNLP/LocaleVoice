# Darija Retrieval Diagnostic — Five No-Evidence Questions

Date: 2026-10-30. Corpus: m2-1.0.0 (3 Feedipedia feed excerpts).
Method: each question run through the real `tokenize` → `retrieve` →
`answer_question` path. No model calls were made for any of the five.

## 1. Per-question diagnostic

Language inference for all five: `darija-or-arabic (arabic-script,
uncertain)`, uncertain=True. The detector sees Arabic script only; it
does not distinguish Darija from MSA and claims no confidence beyond
that. This is a documented limitation, not a failure.

| # | Original | Normalized | Tokens | Retrieved | Decision | Chat call |
|---|----------|------------|--------|-----------|----------|-----------|
| 1 | شنو هي أحسن المزروعات فهاد المنطقة؟ | شنو هي احسن المزروعات فهاد المنطقه | احسن، مزروعات، فهاد، منطقه | none | insufficient | no |
| 2 | كيفاش دايرة الحالة ديال الأرض هاد العام؟ | كيفاش دايره الحاله ديال الارض هاد العام | كيفاش، دايره، حاله، ارض، عام | none | insufficient | no |
| 3 | واش التساقطات كانت كافية للموسم الفلاحي؟ | واش التساقطات كانت كافيه للموسم الفلاحي | تساقطات، كافيه، للموسم، فلاحي | none | insufficient | no |
| 4 | شحال كتسقي الزرع فالسيمانة؟ | شحال كتسقي الزرع فالسيمانه | شحال، كتسقي، زرع، فالسيمانه | none | insufficient | no |
| 5 | شنو هي المشاكل لي كتعاني منها فالفلاحة؟ | شنو هي المشاكل لي كتعاني منها فالفلاحه | مشاكل، لي، كتعاني، منها، فالفلاحه | none | insufficient | no |

Failing stage for all five: **retrieval** (every document scores 0).
The gate then behaves exactly as designed: abstain, no chat call.

## 2. Root cause per question

Corpus vocabulary that could ever match: English feed-nutrition prose
plus aliases {niébé, dolique, اللوبياء, olivier, الزيتون, tourteau,
blé, froment, قمح}. None of the five questions shares a content token
with any document, and — more fundamentally — no document covers any
question's topic:

1. **Best crops for a region** — location-dependent; corpus has no
   regional agronomy content. Unanswerable from this corpus at any
   retrieval quality.
2. **Soil condition this year** — needs soil-test data or field
   observations; corpus has no soil content.
3. **Rainfall sufficiency** — weather/seasonal and inherently
   local-temporal; corpus has no weather content (and static excerpts
   could never answer it).
4. **Irrigation frequency** — crop-management; needs the crop, then an
   irrigation reference the corpus lacks. Note the trap: token زرع
   (cultivation, generic) must NOT be aliased to the wheat document —
   that would ground irrigation advice in a feed-nutrition excerpt
   (false grounding, demonstrated in §4).
5. **Problems faced in farming** — conversational/diagnostic, not a
   document-search query at all. No retrieval improvement answers it;
   it needs an interactive turn.

Cross-cutting causes: (a) topical coverage gap, the dominant factor;
(b) lexical gap for Darija function/content words with no corpus
counterpart; (c) question-type gap — three questions need missing
context (location/season/crop/soil data) and one is conversational.

## 3. What was changed (minimal, gate-preserving)

New `pipeline/clarify.py`: transparent keyword rules over normalized
tokens classify no-evidence questions into `location-dependent-context`,
`soil-context`, `weather-seasonal-context`, `crop-management-context`,
`farmer-diagnostic`, or `generic`. The pipeline's no-evidence branch
now returns the matching clarification message (recorded in
`AnswerResult.clarification_category`) instead of the generic
rejection. Still no model call, no citations, no agricultural claims —
verified by tests. The generic message is unchanged for truly
out-of-domain questions. Clarification wording is approximate Darija
and needs human review before production use.

Also added `much/many/more/most` to the stopword filter after the
Phase 4 experiment showed `much` spuriously matching the wheat doc.

## 4. Multilingual retrieval options evaluated (no replacement made)

Benchmark: the five questions above, originals only, plus UNVERIFIED
author English translations kept strictly separate (never treated as
meaning, never written back).

- **Current normalization + lexical retrieval**: correct abstention on
  all five originals. Precision is good; recall is bounded by coverage.
- **Curated Darija aliases**: cannot help these five — there is no
  document whose topic matches any question, so every alias would be a
  false grounding (see the زرع→wheat trap in §2). Aliases stay valid
  only for mapping variant names onto genuinely covering documents.
- **Translation-assisted retrieval**: HARMFUL here. English renderings
  retrieved spurious matches — cowpea on `crops`/`season`
  ("hungry-season crop" for a rainfall question!), wheat on `much` and
  on `problems` ("digestive problems" for farmer diagnostics). It
  converts correct abstentions into false groundings. Rejected unless
  paired with topical coverage and a much higher match bar.
- **Hybrid lexical + semantic**: unjustified now. Embeddings cannot
  retrieve documents that do not exist; the binding constraint is
  corpus coverage, not matching technology. Revisit after expansion.

## 5. Proposed architecture (for approval, not implemented)

1. **Question router (before retrieval)**: conversational/diagnostic
   detection → interactive turn; context-dependent patterns
   (location/season/crop/soil-data) → clarification turn (this
   milestone's keyword layer is the seed); knowledge questions →
   retrieval as today.
2. **Corpus expansion first**, at the existing provenance bar:
   Moroccan regional crop guides, soil-testing references, irrigation
   references. Weather stays a clarification (dynamic data).
3. **Retrieval upgrades only after (2)**, measured against a
   human-reviewed benchmark: curated alias table with per-alias
   provenance, then optionally translation-assisted or hybrid with a
   raised match bar and false-positive tracking.
4. **Conversation state**: carry answers to clarifications (province,
   crop, season) into the next retrieval turn. Requires the UI session
   work, not just the pipeline.

## 6. Prioritized implementation plan

1. Human review of the five clarification strings (Darija quality).
2. Collect 10–20 consented Darija questions as a versioned benchmark
   with expected categories (reuse `data/evaluation/speech/` consent
   workflow for spoken ones).
3. Expand the corpus per §5(2); each addition must flip a benchmark
   question from clarify/abstain to grounded, or be rejected.
4. Re-run the §4 comparison on the benchmark; adopt the cheapest
   retrieval upgrade that improves recall without false groundings.
5. Conversation state for clarification answers (needs UI + pipeline
   design approval).

## 7. Regression tests

`tests/test_clarification.py` (9 tests): each of the five questions
asserts its category, abstention, no chat call, no citations, and no
evidence; evidence-available Darija control still answers with a model
call; out-of-domain control keeps the generic message; all
clarification strings citation-free. Final suite: **118 passed**.

## 8. Follow-up (Milestone 4B)

Single-turn clarifications became stateful conversations
(`pipeline/conversation.py`): the original question, category, turns,
responses, accumulated context, evidence, and status persist across
farmer replies, and each reply retries retrieval over original +
context. Still-missing abstention wording lives in
`clarify.STILL_MISSING` (HUMAN REVIEW PENDING). Suite: 137 passed.

## 9b. Follow-up (Milestone 4D)

- Greetings/thanks no longer abstain: deterministic intent layer
  resolves them instantly with no model call (wording PENDING review).
- Corpus grew to 4 excerpts (alfalfa, pending second-person review)
  under the structured schema; the §4 verdict stands (coverage, not
  matching, is the binding constraint; translation-assist rejected).
- Every result carries an evidence trace; citation containment is
  validated post-generation and reported (not a factual-verification
  claim). Suite: 183 passed; offline eval 7/7.

## 9. Validation status (Milestone 4C)

- Rollback integrity proven by test (fail-fail-succeed, exactly-once
  state); closed conversations reject responses.
- Browser checklist corrected and extended; all steps BLOCKED here.
- Darija strings extracted to `docs/08-darija-language-review.md`,
  all PENDING; none rewritten.
- Speech workflow ready with zero samples; no WER/CER anywhere.
- First human round defined in `docs/09-human-validation-protocol.md`,
  not yet run. No real-world human validation has occurred.
