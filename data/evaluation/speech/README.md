# Darija Speech Evaluation — Consent, Storage, and Workflow

This directory holds the Milestone 4A speech-evaluation workflow. It currently
contains **no recordings and no transcripts**.

## Directory layout

- `samples.json` — versioned sample records (metadata + transcripts, never audio).
- `audio/` — local-only recordings. **Git-ignored.** Never commit audio here
  without explicit approval and appropriate consent.

## Consent rules

- A sample is usable only when `consent_status` is `granted`.
- `pending`, `declined`, and `withdrawn` samples must not be transcribed,
  evaluated, or shared. `withdrawn` means: delete the audio and remove the
  transcripts from the record.
- `permitted_use` states what the speaker agreed to (e.g.
  `"prototype evaluation only, no redistribution"`). Do not exceed it.

## Local storage, retention, deletion

- Keep recordings in `audio/` on your own machine only; do not upload them
  anywhere except the configured hosted ASR endpoint during an evaluation run.
- File names must be anonymous sample IDs (e.g. `dvq-001.wav`), never a
  person's name.
- Retention: delete recordings once their evaluation notes are recorded,
  unless consent explicitly permits longer storage.
- Deletion: remove the file from `audio/` and clear `asr_transcript` /
  `corrected_transcript` from the sample record on request or withdrawal.

## Workflow

1. Record with consent; save as `audio/<sample-id>.wav` (WAV only).
2. Add a record to `samples.json` (see template below) with
   `reference_transcript` filled in by a human listener.
3. Run the offline report (no providers touched):
   `python scripts/evaluate_speech.py`
4. For a live ASR run on consented audio:
   `python scripts/evaluate_speech.py --transcribe`
   This fills `asr_transcript` for usable samples missing one, then recomputes.
5. Review WER/CER (computed only where a reference exists), retrieval
   recall, citation containment, and usability notes in the report.

## Record template (TEMPLATE — not data)

```json
{
  "sample_id": "dvq-001",
  "consent_status": "granted",
  "permitted_use": "prototype evaluation only, no redistribution",
  "topic": "wheat feeding for cattle",
  "intended_language": "moroccan-darija",
  "audio_ref": "audio/dvq-001.wav",
  "reference_transcript": "<human-verified transcript>",
  "asr_transcript": null,
  "corrected_transcript": null,
  "expected_evidence_ids": ["feedipedia-wheat-grain"],
  "answer_text": null,
  "answer_citations": null,
  "answer_supplied_ids": null,
  "usability_notes": null
}
```

## Metric notes and limitations

- WER uses the shared search tokenizer (case/punctuation folding, Arabic
  diacritic and alef folding, ال-stripping, stopword removal): it measures
  content-word recovery, not raw orthography. Always report the
  normalization alongside any figure.
- CER is computed on whitespace-stripped raw text.
- Both are null (not zero) when no reference transcript exists.
- ASR, retrieval, grounding, and usability are reported as separate
  sections per sample; a good score in one never implies the others.
