"""LocaleVoice Streamlit app (Milestone 3): voice -> transcript -> grounded answer.

Thin UI over the tested backend. All orchestration lives in
localevoice.ui.flow; answer semantics come from localevoice.pipeline.
Run: streamlit run app.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from localevoice.knowledge.corpus import CorpusError, load_corpus  # noqa: E402
from localevoice.pipeline.answer import AnswerResult  # noqa: E402
from localevoice.pipeline.conversation import (  # noqa: E402
    ANSWERED,
    AWAITING_CLARIFICATION,
    Conversation,
    finish_conversation,
    respond_to_clarification,
    start_conversation,
)
from localevoice.pipeline.intent import UNSUPPORTED_GENERAL  # noqa: E402
from localevoice.ui.flow import (  # noqa: E402
    safe_html_paragraph,
    transcribe_upload,
    validate_audio_upload,
)

load_dotenv()

st.set_page_config(
    page_title="LocaleVoice", page_icon="🌾", layout="centered"
)

st.markdown(
    """
    <style>
    .lv-transcript { font-size: 1.15rem; line-height: 1.7; }
    .lv-answer { font-size: 1.1rem; line-height: 1.75; }
    .lv-note { opacity: 0.75; font-size: 0.9rem; }
    textarea { font-size: 1.1rem !important; line-height: 1.7 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_corpus():
    return load_corpus(
        os.path.join(os.path.dirname(__file__), "data", "knowledge")
    )


def reset_to_ask() -> None:
    for key in (
        "recognized",
        "draft",
        "result",
        "conversation",
        "reply",
        "failure",
        "failure_detail",
        "audio_name",
    ):
        st.session_state.pop(key, None)
    st.session_state.stage = "ask"


def fail(message: str, detail: str = "") -> None:
    st.session_state.failure = message
    st.session_state.failure_detail = detail


def show_failure() -> None:
    message = st.session_state.get("failure")
    if not message:
        return
    st.error(f"Something went wrong. {message}")
    detail = st.session_state.get("failure_detail")
    if detail:
        with st.expander("Technical detail"):
            st.code(detail)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("↺ Retry", use_container_width=True, key="fail_retry"):
            st.session_state.pop("failure", None)
            st.session_state.pop("failure_detail", None)
            st.rerun()
    with col_b:
        if st.button("Start over", use_container_width=True, key="fail_restart"):
            reset_to_ask()
            st.rerun()


def render_evidence(result: AnswerResult) -> None:
    if not result.evidence:
        st.info("No evidence was used for this answer.")
        return
    st.subheader("Sources")
    for item in result.evidence:
        with st.expander(f"[{item['document_id']}] {item['title']}"):
            st.write(f"**Publisher:** {item['publisher']}")
            st.write(f"**Category:** {item.get('category', '—')}")
            st.write(f"**Match score:** {item['score']}")
            st.write(f"**Matched terms:** {', '.join(item['matched_terms'])}")
            st.write(f"**Source:** {item['source_url']}")


def handle_audio(filename: str | None, data: bytes | None) -> None:
    try:
        upload = validate_audio_upload(filename, data)
    except ValueError as exc:
        fail(str(exc))
        return
    with st.spinner("Transcribing your recording…"):
        try:
            transcript = transcribe_upload(upload)
        except Exception as exc:  # noqa: BLE001 - rendered honestly below
            fail(
                "Transcription failed. Check your connection and API key, "
                "then retry.",
                f"{type(exc).__name__}: {exc}",
            )
            return
    st.session_state.recognized = transcript
    st.session_state.draft = transcript
    st.session_state.stage = "review"


def handle_confirm() -> None:
    draft = st.session_state.get("draft", "")
    if not draft or not draft.strip():
        fail(
            "The confirmed text is empty. Edit the transcript or type a "
            "question before asking for an answer."
        )
        return
    with st.spinner("Finding evidence and generating your answer…"):
        try:
            conversation = start_conversation(draft, get_corpus())
        except Exception as exc:  # noqa: BLE001 - rendered honestly below
            fail(
                "Answer generation failed. Check your connection and API "
                "key, then retry.",
                f"{type(exc).__name__}: {exc}",
            )
            return
    result = conversation.result
    if result is not None and result.error:
        fail(
            "Answer generation failed and no answer is available.",
            f"{result.error['type']}: {result.error['message']}",
        )
        return
    st.session_state.conversation = conversation
    st.session_state.result = result
    if conversation.status == AWAITING_CLARIFICATION:
        st.session_state.stage = "clarify"
    else:
        st.session_state.stage = "answer"


def handle_reply() -> None:
    conversation = st.session_state.get("conversation")
    if conversation is None:
        reset_to_ask()
        return
    reply = st.session_state.get("reply", "")
    with st.spinner("Searching with your context…"):
        try:
            respond_to_clarification(conversation, reply, get_corpus())
        except ValueError as exc:
            fail(str(exc))
            return
        except Exception as exc:  # noqa: BLE001 - rendered honestly below
            fail(
                "Answer generation failed. Check your connection and API "
                "key, then retry.",
                f"{type(exc).__name__}: {exc}",
            )
            return
    result = conversation.result
    if result is not None and result.error:
        fail(
            "Answer generation failed and no answer is available.",
            f"{result.error['type']}: {result.error['message']}",
        )
        return
    st.session_state.conversation = conversation
    st.session_state.result = result
    if conversation.status == ANSWERED:
        st.session_state.stage = "answer"


def render_trace(conversation: Conversation) -> None:
    for turn in conversation.turns:
        who = "You" if turn.role == "farmer" else "LocaleVoice"
        st.markdown(f"**{who}:**")
        st.markdown(
            safe_html_paragraph(turn.text, "lv-transcript"),
            unsafe_allow_html=True,
        )


try:
    corpus = get_corpus()
except CorpusError as exc:
    st.title("LocaleVoice 🌾")
    st.error(
        "The reference library could not be loaded, so no answers can be "
        "generated."
    )
    with st.expander("Technical detail"):
        st.code(f"CorpusError: {exc}")
    st.stop()

if not corpus.documents:
    st.title("LocaleVoice 🌾")
    st.error("The reference library is empty, so no answers can be generated.")
    st.stop()

if "stage" not in st.session_state:
    st.session_state.stage = "ask"

st.title("LocaleVoice 🌾")
stage = st.session_state.stage

if stage == "ask":
    st.write(
        "Ask a farming question in Darija. Upload a short WAV recording, "
        "record one now, or type your question."
    )
    st.markdown(
        '<p class="lv-note">Recordings are sent to hosted Meta services for '
        "transcription. Only use recordings you are allowed to share.</p>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Upload a WAV recording", type=["wav"])
    if uploaded is not None:
        st.audio(uploaded.getvalue(), format="audio/wav")
    if uploaded is not None and st.button(
        "Transcribe upload", type="primary", use_container_width=True,
        key="ask_transcribe_upload"
    ):
        handle_audio(uploaded.name, uploaded.getvalue())
        st.rerun()
    st.divider()
    recorded = st.audio_input("Or record now")
    if recorded is not None and st.button(
        "Transcribe recording", use_container_width=True, key="ask_transcribe_record"
    ):
        handle_audio(
            getattr(recorded, "name", None) or "recording.wav",
            recorded.getvalue(),
        )
        st.rerun()
    st.divider()
    with st.expander("Or type your question instead"):
        typed = st.text_area("Your question", key="typed")
        if st.button("Continue with typed text", use_container_width=True,
                   key="ask_typed_continue"):
            if not typed or not typed.strip():
                fail("Type a question before continuing.")
            else:
                st.session_state.recognized = ""
                st.session_state.draft = typed.strip()
                st.session_state.stage = "review"
            st.rerun()
    show_failure()

elif stage == "review":
    st.header("Review")
    recognized = st.session_state.get("recognized", "")
    if recognized:
        st.markdown("**Recognized transcript** (what the system heard):")
        st.markdown(
            safe_html_paragraph(recognized, "lv-transcript"),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p class="lv-note">Typed question — no transcription involved.</p>',
            unsafe_allow_html=True,
        )
    st.markdown("**Your corrected version** (this is what gets answered):")
    st.session_state.draft = st.text_area(
        "Corrected transcript",
        value=st.session_state.get("draft", ""),
        height=160,
        label_visibility="collapsed",
    )
    st.markdown(
        '<p class="lv-note">Automatic transcription can make mistakes, and '
        "Darija recognition is not yet validated — please correct any errors "
        "before continuing.</p>",
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✓ Confirm & get answer", type="primary", use_container_width=True,
                       key="review_confirm"):
            handle_confirm()
            st.rerun()
    with col_b:
        if st.button("↺ Re-record", use_container_width=True, key="review_rerecord"):
            reset_to_ask()
            st.rerun()
    show_failure()

elif stage == "clarify":
    conversation = st.session_state.get("conversation")
    if conversation is None or conversation.status != AWAITING_CLARIFICATION:
        reset_to_ask()
        st.rerun()
    else:
        st.header("One question")
        st.markdown("**The question being clarified:**")
        st.markdown(
            safe_html_paragraph(
                conversation.original_question, "lv-transcript"
            ),
            unsafe_allow_html=True,
        )
        st.divider()
        render_trace(conversation)
        if conversation.clarification_responses:
            st.info(
                "Still no matching evidence. Add more detail below, "
                "or finish without an answer."
            )
        with st.form("reply_form", clear_on_submit=True):
            st.text_area("Your answer", key="reply", height=100)
            send = st.form_submit_button(
                "Send", type="primary", use_container_width=True, key="clarify_send"
            )
        if send:
            handle_reply()
            st.rerun()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Finish without answer", use_container_width=True,
                       key="clarify_finish"):
                finish_conversation(conversation)
                st.session_state.result = conversation.result
                st.session_state.stage = "answer"
                st.rerun()
        with col_b:
            if st.button("Start over", use_container_width=True, key="clarify_restart"):
                reset_to_ask()
                st.rerun()
        show_failure()

elif stage == "answer":
    result: AnswerResult | None = st.session_state.get("result")
    if result is None:
        reset_to_ask()
        st.rerun()
    else:
        st.header("Answer")
        conversation = st.session_state.get("conversation")
        if conversation is not None and len(conversation.turns) > 1:
            with st.expander("Conversation", expanded=False):
                render_trace(conversation)
        lang = result.language
        st.markdown(
            f'<p class="lv-note">Question language: {lang.inferred}'
            + (f" (you asked for: {lang.requested})" if lang.requested else "")
            + "</p>",
            unsafe_allow_html=True,
        )
        if result.intent == UNSUPPORTED_GENERAL:
            st.info(
                "Outside agricultural scope. LocaleVoice currently "
                "focuses on farming questions."
            )
        elif result.insufficient_evidence:
            st.warning("Not enough evidence to answer.")
        st.markdown(
            safe_html_paragraph(result.answer_text, "lv-answer"),
            unsafe_allow_html=True,
        )
        render_evidence(result)
        if result.model:
            st.caption(f"Model: {result.model} · {result.elapsed_ms} ms")
        check = (result.trace or {}).get("citation_check")
        if check is not None:
            found = check.get("found") or []
            invalid = check.get("invalid") or []
            if invalid:
                st.caption(
                    f"Citation check: {len(invalid)} citation(s) not in "
                    f"supplied sources: {', '.join(invalid)}"
                )
            elif found:
                st.caption(
                    f"Citation check: {len(found)}/{len(found)} "
                    "citation(s) from supplied sources."
                )
            else:
                st.caption("Citation check: no citations found in the answer.")
        if result.trace:
            with st.expander("Developer diagnostics"):
                st.json(result.trace)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Ask another question", type="primary", use_container_width=True,
                       key="answer_again"):
                reset_to_ask()
                st.rerun()
        with col_b:
            if st.button("↺ Retry answer", use_container_width=True, key="answer_retry"):
                handle_confirm()
                st.rerun()
        show_failure()
