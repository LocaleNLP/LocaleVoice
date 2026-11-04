# LocaleVoice

Voice-first Moroccan Darija agricultural assistant (hackathon MVP).

Milestone 3 adds a working Streamlit interface over the Milestone 2
backend: upload or record a question, review the transcript, and get an
answer grounded strictly in retrieved evidence — with honest
insufficient-evidence behavior. The six documents in `docs/` are the
system of record.

## Setup

Python 3.10 or later. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set a real MODEL_API_KEY.
```

## Run the app

```bash
source .venv/bin/activate
streamlit run app.py
```

Then open the local URL Streamlit prints (usually
http://localhost:8501) in your browser. Upload a short WAV recording
(or record in the browser, or type a question), review the transcript,
and confirm to get a grounded answer.

## Browser verification checklist (manual, local)

Automated UI flows run headlessly in `tests/test_app.py`, but they are
not browser verification. On your machine, with a real browser:

1. `streamlit run app.py` — app loads with no errors; title shows.
2. Upload a short WAV — the player appears and the audio plays back;
   Transcribe reaches Review. (Live ASR call.)
3. Record in the browser — the widget plays back; confirm the recording
   transcribes (bytes are validated as WAV; anything else gets an
   honest re-upload message). (Live ASR call.)
4. Review — recognized text is read-only, corrected text is editable;
   Confirm reaches Answer, or the One-question screen when context is
   missing. Confirming empty text shows a clear message and stays.
5. Typed fallback — type a question and continue; confirm, then answer
   or clarify as appropriate.
6. Sources — each evidence expander shows ID, title, publisher, score,
   matched terms, and source URL.
7. No-evidence — ask something off-corpus (e.g. capital of Morocco);
   the warning shows and no answer is fabricated. (No live call.)
8. Failures — try invalid content, an oversize file, and (optionally)
   an invalid key: each shows a clear message with Retry / Start-over.
9. Layout — repeat steps 2–7 in a narrow/mobile-sized window.
10. Clarification turn — type `شحال كتسقي الزرع فالسيمانة؟`, confirm,
    and check the "One question" screen shows the original question
    plus the conversation so far.
11. Reply with context — answer `القمح`; an evidence-backed answer
    with the wheat source should appear. (Live chat call.)
12. Reply without evidence — restart, ask about rainfall, reply with a
    location; the still-missing note should show and the conversation
    should stay open. Reply a second time to confirm multiple
    responses accumulate, then Finish and Start over to confirm a
    clean restart.
13. Trace — on the Answer screen, the Conversation expander shows every
    turn in order.

Record each step as PASS/FAIL/BLOCKED with the observed behavior.

Verification status: all 13 steps are BLOCKED in the development
sandbox (no server sockets, no browser); none has been run in a real
browser yet. Steps 2, 3, and 11 make live Meta API calls.

## Tests (no network, no paid calls)

```bash
python -m pytest -q
```

All 139 unit tests mock the SDK/HTTP boundary, so this needs no API key
and no network access.

## Corpus validation (offline)

```bash
python scripts/validate_corpus.py
```

## Sample CLI question (offline, no-evidence path)

```bash
python scripts/answer_question.py --question "شنو هي عاصمة المغرب؟"
```

## Real Meta-powered answer run (live API call)

```bash
python scripts/answer_question.py --question "القمح واش مزيان للبقر؟" --save /tmp/run.json
```

Options: `--language`, `--top-k`, `--corpus-dir`, `--save`. A live call is
made only when relevant evidence is found.

## Evaluation

Offline (no API calls, checks retrieval recall + gating):

```bash
python scripts/evaluate_pipeline.py
```

Live (real Meta answers; checks citation containment, latency, model):

```bash
python scripts/evaluate_pipeline.py --live --output /tmp/eval.json
```

## Speech evaluation (Darija readiness)

```bash
python scripts/evaluate_speech.py
python scripts/evaluate_speech.py --transcribe --output /tmp/speech.json
```

Offline by default. See `data/evaluation/speech/README.md` for the
consent, storage, retention, and deletion rules. Recordings live in
`data/evaluation/speech/audio/` (Git-ignored) and are never committed.
No samples collected yet; WER/CER stay null until human-verified
references exist.

## Milestone 1 smoke tests (live)

```bash
python scripts/verify_meta_chat.py
python scripts/transcribe_file.py PATH_TO_WAV
```

Optional Arabic recognizer hint (a hint only — not guaranteed Darija
recognition):

```bash
LOCALEVOICE_ASR_LANGUAGE_BIAS=ar python scripts/transcribe_file.py PATH_TO_WAV
```

## Language-coverage note

The documented Muse Voice Transcribe language list includes Arabic but does
not explicitly list Moroccan Darija as a separate supported language.
Evaluation fixtures are synthetic and manually authored — not real farmer
data. Real Darija ASR quality is still pending until actual consented
speech has been transcribed and reviewed. See
`docs/02-technical-requirements.md`.

## Layout

- `app.py` — Streamlit UI; `.streamlit/config.toml` — theme
- `docs/01-product-requirements.md` … `docs/06-implementation-plan.md`
- `src/localevoice/providers/` — Meta chat + ASR providers
- `src/localevoice/knowledge/` — corpus loading, validation, retrieval
- `src/localevoice/pipeline/` — grounded answer orchestration
- `src/localevoice/evaluation/` — fixture evaluation + reports
- `src/localevoice/ui/` — UI orchestration (tested, no Streamlit imports)
- `data/knowledge/` — versioned corpus + manifest
- `data/evaluation/` — versioned synthetic fixtures
- `scripts/` — smoke tests, CLI, evaluation, validation
- `tests/` — mocked unit tests
- `data/samples/` — local user-provided audio (Git-ignored, consent-gated)
