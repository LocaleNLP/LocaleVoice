# Speech Validation Matrix + TTS Readiness (Milestone 6B)

## Part A — Real-speech test matrix (all PENDING)

Each row needs a consented recording collected per
`docs/12-audio-collection-guide.md`, a human-verified
`reference_transcript` typed by listening, and a
`docs/13-farmer-tasks.md` session where applicable. Status of every
row: **PENDING — 0 recordings, 0 references, WER/CER null**.
Synthetic tones prove audio plumbing only and never count as speech
validation.

| # | Scenario | Input | What must be observed | Pass bar |
|---|---|---|---|---|
| S1 | Darija mic recording | `st.audio_input`, natural question | Transcript usable; corrections counted | Reference transcribed; WER reported with normalization note |
| S2 | Darija WAV upload | Real 16/24 kHz mono WAV | Same as S1 via upload path | Same as S1; upload≈mic quality |
| S3 | Stereo 44.1/48 kHz WAV | Consumer recorder file | Auto-conversion, then transcript | Converts; transcript matches S2-class quality |
| S4 | MP3 upload | Phone voice memo | Conversion + transcript | Converts; no format error |
| S5 | M4A upload | Phone voice memo | Conversion + transcript | Converts; no format error |
| S6 | Background noise | Courtyard/market recording | Degradation vs S1 noted | WER delta recorded, not hidden |
| S7 | Short vs longer utterances | <3 s and 15–60 s questions | Both transcribe; duration path sane | Both complete; corrections counted |
| S8 | Silence | Silent file | `no_speech` guidance, no crash | Friendly message, retry offered |
| S9 | Unintelligible speech | Heavy dialect/noise | Honest transcript-or-abstain | No fabricated question text |

Rules: never quote WER/CER without a human-verified reference;
`evaluate_speech.py` shows null until references exist. French
code-switching and crop names are expected failure points — record
them in `recognition_notes`, do not smooth them over.

## Part B — TTS provider readiness

No provider selected; the null backend stays until a candidate
passes every gate below with project credentials. Marketing claims
do not count as evidence.

Verification protocol (per candidate):

1. **API reality**: trial key + documented endpoint; synthesize a
   fixed 5-sentence Darija sample (greetings, crop advice with
   French terms, numbers); record latency and cost.
2. **Darija bar**: a competent Darija speaker scores pronunciation
   and intelligibility per sentence (1–5) against the written text;
   MSA-accented rendering of Darija fails unless farmers accept it.
3. **Script**: Arabic-script input renders without mojibake;
   mixed French/Arabic handled or its failure documented.
4. **Playback**: seekable audio (WAV/MP3) playable in desktop and
   mobile browsers; pause/stop via native controls.
5. **Privacy/terms**: data-retention period, training-use opt-out,
   and commercial-use terms read from the provider's current terms
   and recorded here with a date — never assumed.

Candidate shortlist (from docs/16, unverified): Azure Speech
ar-MA voices first (best documented Darija fit), then ElevenLabs,
then OpenAI TTS. Local models stay out (hosted-inference-only
architecture).

Only after a candidate passes all five gates may a
`providers/tts/<provider>.py` module be written, with credentials
in environment variables and live tests clearly labeled.
