# Answer Quality, Grounding & Darija Reliability (Milestone 6C)

## Diagnosis (Phase 1)

Reported symptoms: awkward Darija, mixed fragments ("seres"),
malformed citation ("olive-cake]"), wheat/soil/climate/olive topic
mixing, possibly unsupported claims — despite retrieval + containment
passing. Traced end to end:

1. **Malformed citations were invisible to validation
   (reproduced).** `find_citations` only matches well-formed
   `[...]`, so a truncated `olive-cake]` yielded `found: []`,
   `contained: True`, while the UI rendered the garbage literally.
   Fixed: `find_malformed_citations` + `syntax_ok` in every
   citation check, with a UI warning (not silent success).
2. **No language-consistency enforcement (confirmed by
   inspection).** The prompt asked for Darija but never forbade
   English fragments or repetitions. Fixed at the prompt level;
   deterministic hygiene flags (Latin fragments outside a known
   French/ag allowlist, exact repeated sentences) now ride in the
   trace as advisory signals.
3. **Topic mixing via tangential retrieval (confirmed).** Shared
   livestock vocabulary pulls multi-doc evidence at score 1, and
   the old prompt never said "answer only the question asked".
   Thresholds cannot move without breaking recall, so the fix is a
   prompt rule (use only answering passages; name uncovered parts)
   plus the answer structure below.
4. **Awkward Darija (hypothesis, not reproducible in code).**
   Naturalness cannot be tested deterministically; the prompt was
   tightened (one language, keep technical terms, concise farmer
   tone) but human approval stays pending (docs/08 for canned
   text; generated text needs a reviewer per Section 4).

No screenshot was provided; the regression fixture
(`tests/fixtures/answer_6c_problem.txt`) reconstructs the symptoms
from their written description.

## Prompt changes (Phases 2 + 5)

`SYSTEM_PROMPT` grew from 8 to 12 rules: evidence-only + no general
knowledge; no invented regional/soil/climate facts; exact complete
citations; answer-only-the-question (retrieved ≠ relevant);
multi-part scoping with uncovered parts named; fixed structure
(direct answer → evidence explanation → not covered → supported
next step or specialist → citations, one-sentence disclaimer max);
one-language rule with technical-term preservation.

## Validation limits (stated plainly)

- Citation **containment** proves cited IDs were supplied — not
  that claims are true. Case C2 pins this: fabricated wheat claims
  cited to the olive passage still pass containment.
- Citation **syntax** checking catches truncation and malformed
  brackets; it cannot catch a well-formed citation attached to an
  unrelated claim.
- **Hygiene flags** (Latin fragments, repeated sentences) are
  advisory tripwires, not a naturalness proof. An automated check
  never constitutes Darija approval.
- Claim-level semantic verification is beyond deterministic code
  and is not claimed anywhere.

## Suite (Phase 6)

`tests/test_answer_quality.py`, cases A–L (13 tests, mocked model):
relevant wheat/olive evidence, mismatched-evidence scoping,
no-evidence abstention, incomplete/multi-topic scoping,
unsupported crop, malformed/unknown citations, English fragments,
repeated sentences, clarification-then-unsupported. Each records
retrieved/eligible evidence, model invocation, answer, citation
validation, abstention, and expected-vs-actual outcome.

## Live comparison (Phase 8, 2026-11-04)

Multi-topic Darija question (wheat for cattle + suitable soil and
climate), `muse-spark-1.3`, 37.9 s, wheat evidence only. Output
followed the new structure, cited wheat claims correctly, and
explicitly named soil/climate as uncovered with a specialist
referral. Trace: `contained: true`, `syntax_ok: true`, hygiene
clean, no English fragments, no invented regional facts. This is
one sample under the new prompt — not a quality proof — and
Darija naturalness still awaits a human reviewer.
