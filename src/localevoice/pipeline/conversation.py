"""Stateful multi-turn clarification conversations (Milestone 4B).

A Conversation preserves the original farmer question, the clarification
category, every clarification asked, every farmer response, the
accumulated context, retrieved evidence, and the final status. A
follow-up response is always associated with the original question: on
each farmer turn, retrieval retries over the original question PLUS the
accumulated context.

Grounding is unchanged: answers are generated only when retrieval finds
evidence, through the existing `answer_question` (same gate, same
citations). Clarification-only turns never call the model. When context
still yields nothing, the conversation stays open with a per-category
"what remains unavailable" note (see clarify.STILL_MISSING) so the
farmer can add more detail; `finish_conversation` closes it as
abstained. Generic no-evidence questions abstain immediately.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from localevoice.knowledge.corpus import Corpus
from localevoice.pipeline.answer import AnswerResult, answer_question
from localevoice.pipeline.clarify import GENERIC, STILL_MISSING

AWAITING_CLARIFICATION = "awaiting_clarification"
ANSWERED = "answered"
ABSTAINED = "abstained"


@dataclass
class Turn:
    role: str  # "farmer" or "assistant"
    text: str
    category: str | None = None


@dataclass
class Conversation:
    conversation_id: str
    original_question: str
    clarification_category: str | None
    turns: list[Turn] = field(default_factory=list)
    clarifications_asked: list[str] = field(default_factory=list)
    clarification_responses: list[str] = field(default_factory=list)
    accumulated_context: str = ""
    evidence: list[dict] = field(default_factory=list)
    status: str = AWAITING_CLARIFICATION
    result: AnswerResult | None = None

    def to_record(self) -> dict:
        """Serialize for saving. Never contains API keys."""
        return {
            "conversation_id": self.conversation_id,
            "original_question": self.original_question,
            "clarification_category": self.clarification_category,
            "turns": [asdict(t) for t in self.turns],
            "clarifications_asked": list(self.clarifications_asked),
            "clarification_responses": list(self.clarification_responses),
            "accumulated_context": self.accumulated_context,
            "evidence": [dict(e) for e in self.evidence],
            "status": self.status,
            "result": self.result.to_run_record() if self.result else None,
        }


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def start_conversation(
    question: str,
    corpus: Corpus,
    *,
    chat_fn: Callable[..., str] | None = None,
    top_k: int = 3,
    min_score: int = 1,
    language: str | None = None,
    timeout: float = 90.0,
) -> Conversation:
    """Start a conversation from a confirmed farmer question.

    Evidence found -> answered immediately (single turn). No evidence
    with a clarification category -> awaiting_clarification (no model
    call). No evidence and generic -> abstained immediately.
    """
    if not question or not question.strip():
        raise ValueError("question must be a non-empty string")
    kwargs: dict = {
        "top_k": top_k,
        "min_score": min_score,
        "language": language,
        "timeout": timeout,
    }
    if chat_fn is not None:
        kwargs["chat_fn"] = chat_fn
    result = answer_question(question, corpus, **kwargs)

    conversation = Conversation(
        conversation_id=_new_id(),
        original_question=question,
        clarification_category=result.clarification_category,
        turns=[Turn(role="farmer", text=question)],
    )
    if not result.insufficient_evidence:
        conversation.turns.append(Turn(role="assistant", text=result.answer_text))
        conversation.evidence = list(result.evidence)
        conversation.status = ANSWERED
        conversation.result = result
    elif result.clarification_category and result.clarification_category != GENERIC:
        conversation.turns.append(
            Turn(
                role="assistant",
                text=result.answer_text,
                category=result.clarification_category,
            )
        )
        conversation.clarifications_asked.append(result.answer_text)
        conversation.status = AWAITING_CLARIFICATION
        conversation.result = result
    else:
        conversation.turns.append(Turn(role="assistant", text=result.answer_text))
        conversation.status = ABSTAINED
        conversation.result = result
    return conversation


def respond_to_clarification(
    conversation: Conversation,
    farmer_text: str,
    corpus: Corpus,
    *,
    chat_fn: Callable[..., str] | None = None,
    top_k: int = 3,
    min_score: int = 1,
    language: str | None = None,
    timeout: float = 90.0,
) -> Conversation:
    """Attach a farmer response to the original question and retry.

    Retrieval runs over the original question plus ALL accumulated
    context. Evidence found -> answered. Still nothing -> stays open
    with the per-category still-missing note appended (no model call),
    so the farmer can add more detail or finish. Empty responses and
    responses to closed conversations raise ValueError and change
    nothing.
    """
    if conversation.status != AWAITING_CLARIFICATION:
        raise ValueError(
            f"Conversation is {conversation.status}; start a new one instead."
        )
    if not farmer_text or not farmer_text.strip():
        raise ValueError("Response is empty; describe the missing context.")

    response = farmer_text.strip()
    conversation.turns.append(Turn(role="farmer", text=response))
    conversation.clarification_responses.append(response)
    conversation.accumulated_context = " ".join(conversation.clarification_responses)
    combined = f"{conversation.original_question} {conversation.accumulated_context}"

    kwargs: dict = {
        "top_k": top_k,
        "min_score": min_score,
        "language": language,
        "timeout": timeout,
    }
    if chat_fn is not None:
        kwargs["chat_fn"] = chat_fn
    result = answer_question(combined, corpus, **kwargs)

    if result.error:
        # Roll back this turn so a retry re-sends cleanly; the error
        # result stays readable on `result` but the conversation is open.
        conversation.turns.pop()
        conversation.clarification_responses.pop()
        conversation.accumulated_context = " ".join(
            conversation.clarification_responses
        )
        conversation.status = AWAITING_CLARIFICATION
        conversation.result = result
        return conversation

    if result.insufficient_evidence:
        category = conversation.clarification_category or GENERIC
        result.answer_text = STILL_MISSING.get(category, result.answer_text)
        result.clarification_category = category
        conversation.turns.append(
            Turn(role="assistant", text=result.answer_text, category=category)
        )
        conversation.clarifications_asked.append(result.answer_text)
        conversation.status = AWAITING_CLARIFICATION
        conversation.result = result
    else:
        conversation.turns.append(Turn(role="assistant", text=result.answer_text))
        conversation.evidence = list(result.evidence)
        conversation.status = ANSWERED
        conversation.result = result
    return conversation


def finish_conversation(conversation: Conversation) -> Conversation:
    """Close an open conversation as abstained (farmer is done).

    Answered conversations are returned unchanged; already-abstained
    ones are returned unchanged. Only awaiting conversations change.
    """
    if conversation.status == AWAITING_CLARIFICATION:
        conversation.status = ABSTAINED
    return conversation
