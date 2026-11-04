# Voice Responses + Audio Upload Reliability (Milestone 6A)

## 1. Root cause of the uploaded-audio failure

Both audio paths run identical code (`handle_audio` →
`validate_audio_upload` → `transcribe_upload` → Meta). The only
difference is the bytes:

- **Microphone** (`st.audio_input`, default 16 kHz WAV): mono s16le
  at 16 kHz — conforms to what Meta accepts, so it works.
- **Upload**: validated by filename extension plus 12 magic bytes
  (`RIFF....WAVE`) only. Real-world WAVs are usually stereo
  44.1/48 kHz (sometimes float), which passed validation and were
  sent to Meta.

Proven live (2026-11-04): a stereo 48 kHz WAV gets HTTP 400
`"Unsupported WAV format: channels=2, sampleRate=48000,
bitsPerSample=16; expected mono s16le at 16000 or 24000 Hz"`,
while a mono 24 kHz tone gets HTTP 200. The app then showed the
generic "Check your connection and API key" message — wrong
guidance for a format rejection. No failing user sample was
available, so the byte-level comparison above uses synthesized
tones; the provider's error text names the exact expectation.

Fix: `localevoice/audio/normalize.py` inspects magic bytes plus the
full WAV header and converts non-conforming input to mono s16le
24 kHz via FFmpeg before any provider call. Loop closed live: the
same stereo file that got HTTP 400 now normalizes and returns
HTTP 200 (`no_speech`, correct for a tone).

## 2. Supported formats and limits

Accepted uploads: **WAV, MP3, M4A, WebM** (extension + magic bytes;
actual format detected from bytes, never trusted from the name).
Conforming WAVs (mono s16le, 16/24 kHz) pass through byte-identical;
everything else converts via FFmpeg. Without FFmpeg, only
already-conforming WAVs are accepted.

Limits: 10 MiB input, 120 s duration, 60 s conversion timeout.
Corrupt, empty, over-limit, and OGG/unknown inputs are rejected
with specific user-facing messages. Temp files live in a private
directory removed on every path (success, failure, rejection).

## 3. Meta multipart request format (unchanged, verified)

`POST https://api.meta.ai/v1/asr/transcribe` with
`Authorization: Bearer <key>`, a `request` field holding JSON
(`model`, `mode: PUSH_TO_TALK`, `audioEncoding: WAV`, optional
`language` hint), and an `audio` field holding the WAV file
(`audio/wav`). Failures are now categorized: invalid_audio,
no_speech, too_large, auth, rate_limit, timeout, network,
provider, bad_response, config — each with user guidance plus
safe diagnostics (source, formats, sizes, status code, provider
session id). No audio, transcripts, or keys are ever logged.

## 4. Stale-error fix

`failure` state was write-only: nothing cleared it on success, so
`show_failure()` rendered old errors under later screens — e.g. an
ask-stage transcription failure persisted through mic success and
appeared below the final answer. Now every handler clears failure
state at operation start and on success, errors carry an operation
tag (`transcription`/`answer`), and start-over wipes failures plus
TTS state. Six AppTest regressions pin the required scenarios.

## 5. TTS provider comparison (all UNVERIFIED here)

No Meta TTS endpoint exists (Voice Transcribe is STT-only), so any
voice must come from a third party. No provider has been tested
with project credentials or Darija listening checks; **no provider
is selected**. Comparison from public documentation (Nov 2026):

| Provider | Darija/Arabic fit | Integration | Notes |
|---|---|---|---|
| Azure Speech | ar-MA neural voices documented (Jamal/Mouna) — best documented Darija fit | REST/SDK, key + region | Top candidate to verify first |
| ElevenLabs | Arabic supported, no dialects listed; voice cloning could capture Darija (consent implications) | REST, API key | Verify naturalness + cost |
| OpenAI TTS | No language limit claimed, voices optimized for English; Darija quality unknown | Same SDK already used | Easiest plumbing, weakest fit evidence |
| Google Cloud TTS | Generic Arabic voices; no Darija-specific voice found | REST, GCP key | Weak fit |
| Local models (XTTS etc.) | Possible but violates the hosted-inference-only constraint | n/a | Out of architecture |

Next step to select one: obtain a trial key, synthesize the fixed
Darija sample set, and have a Darija speaker score pronunciation
before writing any provider module.

## 6. What shipped for TTS

Vendor-neutral interface (`providers/tts/`): `TTSProvider`,
`TTSEpisode`, `TTSError`, `speech_text_for()` (strips
`[citation-id]` markers so IDs are never spoken), and
`get_tts_provider()` (env `LOCALEVOICE_TTS_PROVIDER`, default
`null`, unknown names fail closed). The null backend reports
speech as unavailable with a friendly message.

Answer screen: grounded answers only (evidence-backed, no error)
show a "🔊 Listen to answer" control — abstention, unsupported,
and greeting texts are never sent. No autoplay; browser-native
audio controls supply play/pause/stop; generated audio is cached
under a text hash for the session only, so replays never
re-synthesize; failures show a caption and leave the written
answer intact; new conversations clear playback state.

## 7. Validation status

- Mocked tests: 302 passed (48 new: 17 normalize, 12 ASR errors,
  6 stale-error UI, 6 TTS unit, 5 TTS UI, 2 flow).
- Offline evals: 7/7 and 20/20; speech eval 0 samples.
- Live Meta: ASR format rejection reproduced (400) and fixed path
  verified (200); chat untouched this milestone.
- Live TTS: none (no provider selected; null backend only).
- Browser: still BLOCKED (sandbox); AppTest only.
- Human Darija validation: none (0 participants).
