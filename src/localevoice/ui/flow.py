"""UI orchestration for the Streamlit app (Milestone 3).

Pure orchestration over the tested backend: no Streamlit imports here, so
this module is unit-testable offline with injected backend functions.
The UI layer (app.py) handles widgets and session state only.
"""

from __future__ import annotations

import html
import inspect
import os
from collections.abc import Callable
from dataclasses import asdict, dataclass

from localevoice.audio.normalize import (
    MAX_UPLOAD_BYTES,
    SUPPORTED_EXTENSIONS,
    NormalizedAudio,
    sniff_container,
)
from localevoice.knowledge.corpus import Corpus
from localevoice.pipeline.answer import AnswerResult, answer_question
from localevoice.providers.meta_asr import transcribe_file

MAX_AUDIO_BYTES = MAX_UPLOAD_BYTES  # 10 MiB upload cap (single source above)


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    data: bytes
    source: str = "upload"  # "upload" or "microphone", for diagnostics only


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    diagnostics: dict  # safe metadata only: formats, sizes, status, ids


def validate_audio_upload(
    filename: str | None,
    data: bytes | None,
    max_bytes: int = MAX_AUDIO_BYTES,
    source: str = "upload",
) -> ValidatedUpload:
    """Fast pre-check of a recording before normalization.

    Accepts WAV, MP3, M4A, and WebM by extension; the actual container
    is detected from magic bytes. Deep validation (codec, rate,
    channels, duration) happens in NormalizedAudio. Raises ValueError
    with a user-facing message on any problem.
    """
    if not filename or data is None or len(data) == 0:
        raise ValueError("No audio received. Upload a recording and retry.")
    ext = os.path.splitext(filename.lower())[1]
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format ({ext or 'no extension'}). "
            "Upload WAV, MP3, M4A, or WebM."
        )
    if len(data) > max_bytes:
        raise ValueError(
            f"Recording is too large ({len(data) / 1024 / 1024:.1f} MiB). "
            f"Please keep it under {max_bytes / 1024 / 1024:.0f} MiB."
        )
    container = sniff_container(data)
    if container in ("unknown", "ogg"):
        raise ValueError(
            "This file is not a supported audio recording. Upload "
            "WAV, MP3, M4A, or WebM."
        )
    return ValidatedUpload(filename=filename, data=data, source=source)


def transcribe_upload_ex(
    upload: ValidatedUpload,
    transcribe_fn: Callable[..., str] = transcribe_file,
    language_bias: str | None = None,
) -> TranscriptionResult:
    """Normalize then transcribe; return the transcript with diagnostics.

    Diagnostics carry safe metadata only (source, formats, sizes,
    provider status/session id) — never audio, transcripts, or keys.
    Provider and validation errors propagate unchanged for the UI.
    """
    provider_info: dict = {}
    try:
        accepts_diagnostics = "diagnostics" in inspect.signature(
            transcribe_fn
        ).parameters
    except (TypeError, ValueError):
        accepts_diagnostics = False
    with NormalizedAudio(upload.data, upload.filename) as normalized:
        kwargs: dict = {"language_bias": language_bias}
        if accepts_diagnostics:
            kwargs["diagnostics"] = provider_info
        try:
            transcript = transcribe_fn(normalized.path, **kwargs)
        except Exception as exc:
            # The provider failed after normalization: attach what was
            # sent so the UI can show it (safe metadata only).
            exc.diagnostics = {  # type: ignore[attr-defined]
                "input_source": upload.source,
                "original_format": asdict(normalized.original),
                "normalized_format": asdict(normalized.final),
                "converted": normalized.converted,
                "provider": dict(provider_info),
            }
            raise
        diagnostics = {
            "input_source": upload.source,
            "original_format": asdict(normalized.original),
            "normalized_format": asdict(normalized.final),
            "converted": normalized.converted,
            "provider": provider_info,
        }
    return TranscriptionResult(transcript=transcript, diagnostics=diagnostics)


def transcribe_upload(
    upload: ValidatedUpload,
    transcribe_fn: Callable[..., str] = transcribe_file,
    language_bias: str | None = None,
) -> str:
    """Send a validated upload through the ASR provider; return the transcript.

    Provider errors (MetaASRError, FileNotFoundError, ValueError) propagate
    unchanged for the UI to render honestly.
    """
    return transcribe_upload_ex(
        upload, transcribe_fn=transcribe_fn, language_bias=language_bias
    ).transcript


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
