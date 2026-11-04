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

> "We are testing a farming voice assistant. With your permission I
> will record your farming question to check how well the system
> understands speech. The recording stays on this machine, is used
> only for prototype evaluation, and is never shared. You can refuse,
> stop at any time, or ask me to delete your recording afterwards —
> no reason needed. Do you agree?"

- Agreement → `consent_status: "granted"`, `permitted_use:
  "prototype evaluation only, no redistribution"`.
- Refusal or silence → do not record. No record is created.
- Withdrawal later → delete the WAV file and clear
  `reference_transcript`, `asr_transcript`, and
  `corrected_transcript` from the record; set `consent_status:
  "withdrawn"`.

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
