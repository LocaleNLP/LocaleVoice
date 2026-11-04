"""UI orchestration for the Streamlit app (Milestone 3).

Pure orchestration over the tested backend: no Streamlit imports here, so
this module is unit-testable offline with injected backend functions.
The UI layer (app.py) handles widgets and session state only.
"""

from __future__ import annotations

import html
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass

from localevoice.knowledge.corpus import Corpus
from localevoice.pipeline.answer import AnswerResult, answer_question
from localevoice.providers.meta_asr import transcribe_file

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MiB upload cap


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    data: bytes


def validate_audio_upload(
    filename: str | None, data: bytes | None, max_bytes: int = MAX_AUDIO_BYTES
) -> ValidatedUpload:
    """Validate an uploaded recording before any provider call.

    Accepted format: WAV only (the ASR provider requires a `.wav` file).
    Raises ValueError with a user-facing message on any problem.
    """
    if not filename or data is None or len(data) == 0:
        raise ValueError("No audio received. Upload a WAV recording and retry.")
    if not filename.lower().endswith(".wav"):
        raise ValueError(
            f"Only WAV files are supported, got: {filename}. "
            "Please upload a .wav recording."
        )
    if len(data) > max_bytes:
        raise ValueError(
            f"Recording is too large ({len(data) / 1024 / 1024:.1f} MiB). "
            f"Please keep it under {max_bytes / 1024 / 1024:.0f} MiB."
        )
    if len(data) < 44 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError(
            "This file does not look like a WAV recording. "
            "Please upload a valid .wav file."
        )
    return ValidatedUpload(filename=filename, data=data)


def transcribe_upload(
    upload: ValidatedUpload,
    transcribe_fn: Callable[..., str] = transcribe_file,
    language_bias: str | None = None,
) -> str:
    """Send a validated upload through the ASR provider; return the transcript.

    Provider errors (MetaASRError, FileNotFoundError, ValueError) propagate
    unchanged for the UI to render honestly.
    """
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="localevoice-")
    try:
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(upload.data)
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        return transcribe_fn(path, language_bias=language_bias)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def safe_html_paragraph(text: str, css_class: str) -> str:
    """Render user/model text as an escaped HTML paragraph.

    Transcripts and answers are untrusted text; they must never be
    interpolated raw into `unsafe_allow_html` markup.
    """
    return f'<p class="{html.escape(css_class, quote=True)}" dir="auto">' \
        f"{html.escape(text)}</p>"


def answer_confirmed_text(
    question: str,
    corpus: Corpus,
    answer_fn: Callable[..., AnswerResult] = answer_question,
    top_k: int = 3,
    language: str | None = None,
) -> AnswerResult:
    """Pass user-confirmed text to the answer pipeline unchanged.

    Empty text is rejected before any retrieval or model call. Gating,
    grounding, and error semantics all come from the backend untouched.
    """
    if not question or not question.strip():
        raise ValueError(
            "The confirmed text is empty. Edit the transcript or type a "
            "question before asking for an answer."
        )
    return answer_fn(question, corpus, top_k=top_k, language=language)
