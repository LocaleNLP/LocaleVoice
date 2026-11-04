# Darija Language-Review Package (Milestones 4C–5)

Source of truth for wording: `src/localevoice/pipeline/clarify.py`
(`MESSAGES` + `STILL_MISSING`), `src/localevoice/pipeline/intent.py`
(`RESPONSES`), and `src/localevoice/pipeline/answer.py`
(`INSUFFICIENT_EVIDENCE_MESSAGE`). Reviewers edit code-adjacent
wording only through the maintainer: propose corrections below, and
approved text is copied verbatim into the source file. No LLM output
may be recorded as human-reviewed, and no message may be marked
approved except by the named human reviewer.

Status of every message below: **HUMAN REVIEW PENDING**.

## Variety note (read before reviewing)

Target: **Moroccan Darija** as spoken by farmers — not Modern Standard
Arabic. A correction that replaces a Darija form with an MSA form is a
regression, not an improvement. If a message mixes varieties (e.g. an
MSA word inside a Darija sentence), flag which word feels off and say
which variety the replacement belongs to. French/Arabic mixed
expressions are reviewed as spoken: keep code-switching that farmers
actually use (e.g. `blé`, `niébé` next to Arabic), and correct only
what sounds unnatural. Record the variety of each correction in the
review log.

## How to review

1. Read the current wording aloud. Moroccan Darija, farmer audience,
   spoken naturalness matters more than formal grammar.
2. Check the intended meaning matches what the Arabic actually says.
3. Write your correction in the Correction column (leave blank if fine).
4. Mark Approved yes/no and add pronunciation notes (words farmers
   would say differently, regional variants to accept).

## Clarification prompts (MESSAGES)

### CL-ask-crop-management

- Current: باش نعاونك فالسقي، خاصني نعرف شنو زارع. قوليا شنو هي المزروعات لي عندك؟
- Intended: "To help with irrigation, I need to know what you planted. Tell me which crops you have."
- Context: One-question screen, after a no-evidence irrigation question; followed by a free-text reply box.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-ask-weather-seasonal

- Current: التساقطات والموسم الفلاحي كيختلفو من منطقة لمنطقة. قوليا فأي إقليم ولا جماعة، و فأي موسم فلاحي؟
- Intended: "Rainfall and the farming season differ from region to region. Tell me which province or commune, and which farming season."
- Context: One-question screen, after a no-evidence rainfall/season question; followed by a free-text reply box.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-ask-soil

- Current: الحالة ديال الأرض كتحتاج معطيات محلية. واش عندك تحليل ديال التربة، ولا شنو لاحظتي فالأرض هاد العام؟
- Intended: "The state of the land needs local data. Do you have a soil analysis, or what did you observe in the land this year?"
- Context: One-question screen, after a no-evidence soil/land question; followed by a free-text reply box.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-ask-location-dependent

- Current: أحسن المزروعات كتعتمد على المنطقة والتربة والماء. فأي إقليم ولا جماعة الفلاحة ديالك؟
- Intended: "The best crops depend on the region, soil, and water. In which province or commune is your farm?"
- Context: One-question screen, after a no-evidence best-crops-for-region question; followed by a free-text reply box.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-ask-farmer-diagnostic

- Current: مرحبا. باش نعاونك، وصف ليا المشكل: شنو واقع بالضبط، فأي مزروعات، و من إيمتى بدا؟
- Intended: "Hello. To help you, describe the problem: what exactly is happening, in which crops, and when did it start?"
- Context: One-question screen, after a no-evidence farming-problems question; followed by a free-text reply box.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

## Still-missing abstentions (STILL_MISSING)

### CL-miss-crop-management

- Current: شكرا على التوضيح. حتى مع هاد المعطيات، ما لقيتش دليل على السقي فالمراجع المتوفرة، وما نبغيش نخمن. سول المستشار الفلاحي المحلي.
- Intended: "Thanks for clarifying. Even with this information, I found no evidence about irrigation in the available references, and I don't want to guess. Ask the local agricultural advisor."
- Context: Same screen, after the farmer replied but retrieval still found nothing; conversation stays open for more detail.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-miss-weather-seasonal

- Current: شكرا على التوضيح. ما عنديش معطيات التساقطات للمنطقة والموسم ديالك فالمراجع المتوفرة. سول المصالح الفلاحية المحلية.
- Intended: "Thanks for clarifying. I have no rainfall data for your region and season in the available references. Ask the local agricultural services."
- Context: Same screen, after the farmer replied but retrieval still found nothing; conversation stays open for more detail.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-miss-soil

- Current: شكرا على التوضيح. ما عنديش دليل كافي على الحالة ديال الأرض. تحليل التربة عند مختبر محلي هو الخطوة اللازمة.
- Intended: "Thanks for clarifying. I don't have enough evidence about the state of the land. A soil analysis at a local lab is the necessary step."
- Context: Same screen, after the farmer replied but retrieval still found nothing; conversation stays open for more detail.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-miss-location-dependent

- Current: شكرا على التوضيح. ما عنديش دليل على أحسن المزروعات لمنطقتك فالمراجع المتوفرة. سول المستشار الفلاحي المحلي.
- Intended: "Thanks for clarifying. I have no evidence about the best crops for your region in the available references. Ask the local agricultural advisor."
- Context: Same screen, after the farmer replied but retrieval still found nothing; conversation stays open for more detail.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### CL-miss-farmer-diagnostic

- Current: شكرا على التوضيح. ما لقيتش دليل مطابق فالمراجع، وما نبغيش نخمن. وصف الأعراض لبيطري ولا تقني محلي.
- Intended: "Thanks for clarifying. I found no matching evidence in the references, and I don't want to guess. Describe the symptoms to a local vet or technician."
- Context: Same screen, after the farmer replied but retrieval still found nothing; conversation stays open for more detail.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

## Intent responses (Milestone 4D, source: `pipeline/intent.py`)

### IN-greeting

- Current: وعليكم السلام! مرحبا بك في LocaleVoice. كيف نقدر نعاونك اليوم فالفلاحة؟
- Intended: "Peace be upon you too! Welcome to LocaleVoice. How can I help you today with farming?"
- Context: Answer screen, instant reply to a standalone greeting; no model call, no sources shown.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### IN-thanks

- Current: العفو! إلا كان عندك شي سؤال آخر على الفلاحة، مرحبا.
- Intended: "You're welcome! If you have any other question about farming, welcome."
- Context: Answer screen, instant reply to standalone thanks; no model call.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### IN-goodbye

- Current: بسلامة! الله يعاونك فالفلاحة ديالك.
- Intended: "Goodbye! May God help you with your farming."
- Context: Answer screen, instant reply to a standalone farewell; no model call.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

### IN-unsupported-domain

- Current: LocaleVoice حاليا كيجاوب غير على الأسئلة الفلاحة. صيفط ليا سؤال على المزروعات، التربة، السقي، ولا تربية المواشي.
- Intended: "LocaleVoice currently only answers farming questions. Send me a question about crops, soil, irrigation, or livestock raising."
- Context: Answer screen with warning styling, instant reply to a clearly non-agricultural question; no model call.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _
- Final status: PENDING

## Generic abstention (source: `pipeline/answer.py`)

Shown with warning styling whenever retrieval finds nothing and no
clarification topic matches. English sentence with a mixed
wheat/القمح/blé example — review the Arabic fragment and the
code-switch, not the English grammar.

### UI-generic-insufficient

- Current: I could not find relevant evidence for this question in the available reference material, so I will not guess an answer. Try rephrasing with the crop or animal name (for example: wheat/القمح/blé, olive cake, cowpea), or ask your local agricultural advisor.
- Intended: "No evidence found, so no answer will be guessed. Suggestion: rephrase with the crop/animal name, or consult a local advisor."
- Context: Answer screen with warning styling, generic no-evidence path (no clarification topic matched); no model call.
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _ (read the القمح fragment as farmers say it)
- Final status: PENDING

## Review log

| Date | Reviewer | Messages covered | Correction variety (Darija/MSA/mixed) | Outcome |
|------|----------|------------------|----------------------------------------|---------|
| _ | _ | _ | _ | _ |
