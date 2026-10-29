# LocaleVoice

Voice-first Moroccan Darija agricultural assistant (hackathon MVP).

Milestone 2 implements a command-line vertical slice: a versioned
agricultural corpus, deterministic lexical retrieval, and Meta-powered
answer generation grounded strictly in retrieved evidence — with honest
insufficient-evidence behavior and reproducible evaluation. No UI yet.
The six documents in `docs/` are the system of record.

## Setup

Python 3.10 or later. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set a real MODEL_API_KEY.
```

## Tests (no network, no paid calls)

```bash
python -m pytest -q
```

All 65 unit tests mock the SDK/HTTP boundary, so this needs no API key
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

- `docs/01-product-requirements.md` … `docs/06-implementation-plan.md`
- `src/localevoice/providers/` — Meta chat + ASR providers
- `src/localevoice/knowledge/` — corpus loading, validation, retrieval
- `src/localevoice/pipeline/` — grounded answer orchestration
- `src/localevoice/evaluation/` — fixture evaluation + reports
- `data/knowledge/` — versioned corpus + manifest
- `data/evaluation/` — versioned synthetic fixtures
- `scripts/` — smoke tests, CLI, evaluation, validation
- `tests/` — mocked unit tests
- `data/samples/` — local user-provided audio (Git-ignored, consent-gated)
