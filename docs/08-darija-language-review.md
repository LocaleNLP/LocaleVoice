# Darija Language-Review Package (Milestone 4C)

Source of truth for wording: `src/localevoice/pipeline/clarify.py`
(`MESSAGES` + `STILL_MISSING`). Reviewers edit code-adjacent wording
only through the maintainer: propose corrections below, and approved
text is copied verbatim into `clarify.py`. No LLM output may be
recorded as human-reviewed.

Status of every message below: **HUMAN REVIEW PENDING**.

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
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-ask-weather-seasonal

- Current: التساقطات والموسم الفلاحي كيختلفو من منطقة لمنطقة. قوليا فأي إقليم ولا جماعة، و فأي موسم فلاحي؟
- Intended: "Rainfall and the farming season differ from region to region. Tell me which province or commune, and which farming season."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-ask-soil

- Current: الحالة ديال الأرض كتحتاج معطيات محلية. واش عندك تحليل ديال التربة، ولا شنو لاحظتي فالأرض هاد العام؟
- Intended: "The state of the land needs local data. Do you have a soil analysis, or what did you observe in the land this year?"
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-ask-location-dependent

- Current: أحسن المزروعات كتعتمد على المنطقة والتربة والماء. فأي إقليم ولا جماعة الفلاحة ديالك؟
- Intended: "The best crops depend on the region, soil, and water. In which province or commune is your farm?"
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-ask-farmer-diagnostic

- Current: مرحبا. باش نعاونك، وصف ليا المشكل: شنو واقع بالضبط، فأي مزروعات، و من إيمتى بدا؟
- Intended: "Hello. To help you, describe the problem: what exactly is happening, in which crops, and when did it start?"
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

## Still-missing abstentions (STILL_MISSING)

### CL-miss-crop-management

- Current: شكرا على التوضيح. حتى مع هاد المعطيات، ما لقيتش دليل على السقي فالمراجع المتوفرة، وما نبغيش نخمن. سول المستشار الفلاحي المحلي.
- Intended: "Thanks for clarifying. Even with this information, I found no evidence about irrigation in the available references, and I don't want to guess. Ask the local agricultural advisor."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-miss-weather-seasonal

- Current: شكرا على التوضيح. ما عنديش معطيات التساقطات للمنطقة والموسم ديالك فالمراجع المتوفرة. سول المصالح الفلاحية المحلية.
- Intended: "Thanks for clarifying. I have no rainfall data for your region and season in the available references. Ask the local agricultural services."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-miss-soil

- Current: شكرا على التوضيح. ما عنديش دليل كافي على الحالة ديال الأرض. تحليل التربة عند مختبر محلي هو الخطوة اللازمة.
- Intended: "Thanks for clarifying. I don't have enough evidence about the state of the land. A soil analysis at a local lab is the necessary step."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-miss-location-dependent

- Current: شكرا على التوضيح. ما عنديش دليل على أحسن المزروعات لمنطقتك فالمراجع المتوفرة. سول المستشار الفلاحي المحلي.
- Intended: "Thanks for clarifying. I have no evidence about the best crops for your region in the available references. Ask the local agricultural advisor."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### CL-miss-farmer-diagnostic

- Current: شكرا على التوضيح. ما لقيتش دليل مطابق فالمراجع، وما نبغيش نخمن. وصف الأعراض لبيطري ولا تقني محلي.
- Intended: "Thanks for clarifying. I found no matching evidence in the references, and I don't want to guess. Describe the symptoms to a local vet or technician."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

## Intent responses (Milestone 4D, source: `pipeline/intent.py`)

### IN-greeting

- Current: وعليكم السلام! مرحبا بك في LocaleVoice. كيف نقدر نعاونك اليوم فالفلاحة؟
- Intended: "Peace be upon you too! Welcome to LocaleVoice. How can I help you today with farming?"
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### IN-thanks

- Current: العفو! إلا كان عندك شي سؤال آخر على الفلاحة، مرحبا.
- Intended: "You're welcome! If you have any other question about farming, welcome."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### IN-goodbye

- Current: بسلامة! الله يعاونك فالفلاحة ديالك.
- Intended: "Goodbye! May God help you with your farming."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

### IN-unsupported-domain

- Current: LocaleVoice حاليا كيجاوب غير على الأسئلة الفلاحة. صيفط ليا سؤال على المزروعات، التربة، السقي، ولا تربية المواشي.
- Intended: "LocaleVoice currently only answers farming questions. Send me a question about crops, soil, irrigation, or livestock raising."
- Correction: _
- Approved: no (PENDING)
- Pronunciation notes: _

## Review log

| Date | Reviewer | Messages covered | Outcome |
|------|----------|------------------|---------|
| _ | _ | _ | _ |
