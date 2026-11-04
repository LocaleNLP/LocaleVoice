# Audio Collection Guide for Facilitators (Milestone 5)

Goal: collect a small set of consented Moroccan Darija speech samples
so that ASR quality can be measured for the first time. No samples
exist yet; do not invent any.

## Before the session

1. Read `data/evaluation/speech/README.md` (consent, storage,
   retention, deletion). The rules there are binding.
2. Prepare anonymous sample IDs in advance (`dvq-001`, `dvq-002`, …).
   Never use a participant's name in a file name, a record, or notes.
3. Collect the minimum: spoken question audio + consent status. No
   names, phone numbers, locations, or photos.

## Consent script (read aloud, in Darija)

The script must communicate all seven points: (1) purpose, (2) what
data is collected, (3) where it is stored, (4) who can access it,
(5) retention and deletion, (6) voluntary participation, (7) right
to decline or withdraw. No legal-compliance claim is made here;
this is a prototype-evaluation consent, not a legal instrument.

English reference:

> "We are testing a farming voice assistant. [purpose] With your
> permission I will record your farming question — only your voice
> asking the question, nothing else. [what] The recording stays on
> this machine only. [where] Only I, the facilitator, can listen to
> it here; the only other processing is one automatic transcription
> by the hosted speech service when we evaluate. [who] I will delete
> the recording once my evaluation notes are done, unless you allow
> longer storage; you can ask me to delete it at any time and I will
> do so immediately. [retention/deletion] Taking part is completely
> voluntary. [voluntary] You can refuse, stop at any time, or
> withdraw afterwards — no reason needed, and it changes nothing
> about how we treat you. [decline/withdraw] Do you agree?"

Darija version — **HUMAN REVIEW PENDING. Do not use with
participants until a competent Darija reviewer approves it.** Until
then, explain the seven points above in the participant's language
from the English reference.

> "كنجربو مساعد صوتي للفلاحة. إلا وافقتي، غنسجل السؤال الفلاحي
> ديالك — غير الصوت ديالك وانت كتسول، حتى حاجة أخرى. التسجيل
> كيبقى فهاد الحاسوب غير. غير أنا لي نسمع ليه هنا؛ المعالجة
> الوحيدة الأخرى هي تحويل الصوت لنص مرة وحدة ملي نديرو التقييم.
> غنمسح التسجيل ملي نكمل الملاحظات ديال التقييم، إلا سمحتي نخليه
> كتر؛ وتقدر تطلب مني نمسحو فأي وقت وغنمسحو فالحين. المشاركة
> تطوعية تماما. تقدر ترفض، ولا تحبس فأي وقت، ولا تراجع الموافقة
> من بعد — بلا ما تعطي حتى سبب، وما غيبدل حتى حاجة. واش موافق؟"

- Agreement → `consent_status: "granted"`, `permitted_use:
  "prototype evaluation only, no redistribution"`.
- Refusal or silence → do not record. No record is created.
- Withdrawal later → follow the deletion procedure below.

## Withdrawal and deletion procedure

When a participant withdraws (during or after the session), the
facilitator — not automation — performs these steps in order.
Nothing is deleted automatically.

1. In `samples.json`, set the sample's `consent_status` to
   `"withdrawn"`. From this moment the code refuses to transcribe,
   score, or retrieve over it (`test_non_granted_samples_are_never_scored`).
2. Delete the audio file from `audio/`.
3. Clear `reference_transcript`, `asr_transcript`, and
   `corrected_transcript` (set to `null`). Keep `sample_id`,
   `topic`, and consent fields: the record now proves a sample
   existed and was withdrawn, without retaining speech content.
4. Check `usability_notes` and `recognition_notes`: remove any
   verbatim participant speech pasted there. Notes must describe
   errors ("dropped final syllable"), never quote the speaker.
5. Delete any saved evaluation reports that predate the withdrawal
   (they may contain scores derived from the sample) and re-run
   `python scripts/evaluate_speech.py` to confirm the sample now
   reports `usable=false`, `wer=null`, `cer=null`.
6. Confirm to the participant that everything is deleted.

Evaluation reports never contain audio or transcript text — only
sample IDs, presence flags, scores, and facilitator notes — so a
regenerated report cannot leak withdrawn speech content.

## Recording

1. Quiet place if possible; note the real conditions in
   `recording_context` (e.g. "courtyard, phone mic, chickens").
2. Ask the participant to speak one natural farming question (their
   own words — see the task sheet in `docs/13-farmer-tasks.md`).
   Do not coach wording.
3. Save as `data/evaluation/speech/audio/<sample-id>.wav` (WAV,
   mono or stereo, any sample rate the app accepts).
4. Confirm the file plays back before the participant leaves.

## After the session

1. Listen to each recording and type exactly what was said into
   `reference_transcript`. This human-verified transcript is the
   ground truth: WER/CER cannot be computed without it, and the
   report shows null (not zero) until it exists.
2. Fill `topic`, `intended_language` (e.g. `moroccan-darija`), and
   `expected_evidence_ids` (doc IDs, or `[]` if the question is
   outside the 4 excerpts).
3. Run the offline report (no providers, no cost):
   `python scripts/evaluate_speech.py`
4. Only when every sample is consented: run the live transcription:
   `python scripts/evaluate_speech.py --transcribe`
   This sends audio to the hosted ASR endpoint once per sample and
   saves `asr_transcript` back into `samples.json`. It transcribes
   granted samples only.
5. Read the ASR output against your reference; write
   `recognition_notes` (what words failed, e.g. French crop names,
   numbers, dialect forms). Copy the participant's own correction,
   if they gave one, into `corrected_transcript`.
6. Re-run the offline report and record WER/CER with the
   normalization note from the speech README (tokenizer-based WER
   measures content-word recovery, not raw orthography).

## Prohibited

- Committing audio or transcripts with personal identifiers to Git
  (`audio/` is Git-ignored; keep it that way).
- Computing or quoting WER/CER from references you did not verify
  by listening.
- Reusing a recording beyond its `permitted_use`.
- Keeping a withdrawn participant's audio or transcripts.
