from __future__ import annotations

import json
from typing import Generator, Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ai_interaction import AIInteraction
from app.schemas.ai_assistant import AIChatRequest, AIChatResponse
from app.services.ai_agent import generate_recommendations, stream_recommendations
from app.services.auth_service import decode_access_token
from app.services.user_service import get_user_by_id

router = APIRouter()


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _resolve_user(db: Session, authorization: Optional[str]):
    if not authorization:
        return None
    try:
        token = authorization.split(" ", 1)[1]
        user_id = decode_access_token(token)
        return get_user_by_id(db, user_id)
    except Exception:
        return None


def _initial_conversation(payload: AIChatRequest):
    return payload.conversation_history or []


def _persist_interaction_start(db: Session, payload: AIChatRequest, user) -> AIInteraction:
    interaction = AIInteraction(
        user_id=user.id if user else None,
        query=payload.message,
        conversation_history=_initial_conversation(payload),
        assistant_text=None,
        recommendations=None,
        meta={"status": "pending"},
    )
    db.add(interaction)
    db.flush()
    return interaction


def _finalize_interaction(
    db: Session,
    interaction: AIInteraction,
    conversation_history,
    assistant_text: str,
    recommendations,
):
    try:
        interaction.assistant_text = assistant_text
        interaction.recommendations = recommendations
        interaction.conversation_history = conversation_history
        interaction.meta = {
            "status": "done",
            "summary": (assistant_text or "")[:200],
            "recommendation_count": len(recommendations or []),
        }
        db.add(interaction)
        db.commit()
    except Exception:
        db.rollback()


@router.post("/chat", response_model=AIChatResponse)
def chat_endpoint(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Canonical JSON endpoint required by the assignment spec."""
    user = _resolve_user(db, authorization)
    interaction = _persist_interaction_start(db, payload, user)

    if not (payload.message or "").strip():
        name = getattr(user, "name", None) if user else None
        greeting = f"Hi {name}!" if name else "Hi there!"
        greeting += " Ask me for restaurant ideas, current hours, or a follow-up like 'show me something cheaper'."
        conversation_history = _initial_conversation(payload) + [{"role": "assistant", "content": greeting}]
        _finalize_interaction(db, interaction, conversation_history, greeting, [])
        return {
            "assistant_text": greeting,
            "recommendations": [],
            "conversation_history": conversation_history,
        }

    assistant_text, recommendations = generate_recommendations(
        db,
        user,
        payload.message,
        payload.conversation_history,
    )
    conversation_history = _initial_conversation(payload) + [
        {
            "role": "user",
            "content": payload.message,
        },
        {
            "role": "assistant",
            "content": assistant_text,
            "recommendations": recommendations,
        },
    ]
    _finalize_interaction(db, interaction, conversation_history, assistant_text, recommendations)
    return {
        "assistant_text": assistant_text,
        "recommendations": recommendations,
        "conversation_history": conversation_history,
    }


@router.post("/chat/json", response_model=AIChatResponse)
def chat_json_endpoint(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Backward-compatible alias for older clients."""
    return chat_endpoint(payload, db, authorization)


@router.post("/chat/stream")
def chat_stream_endpoint(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    user = _resolve_user(db, authorization)

    def event_stream() -> Generator[str, None, None]:
        interaction = _persist_interaction_start(db, payload, user)
        yield _sse_event({"type": "start", "message": "stream_start"})

        if not (payload.message or "").strip():
            name = getattr(user, "name", None) if user else None
            greeting = f"Hi {name}!" if name else "Hi there!"
            greeting += " Ask me for restaurant ideas, current hours, or a follow-up like 'show me something cheaper'."
            conversation_history = _initial_conversation(payload) + [{"role": "assistant", "content": greeting}]
            _finalize_interaction(db, interaction, conversation_history, greeting, [])
            yield _sse_event({"type": "assistant_chunk", "text": greeting})
            yield _sse_event({"type": "done", "conversation_history": conversation_history})
            return

        assistant_text = ""
        recommendations = []
        try:
            generator = stream_recommendations(db, user, payload.message, payload.conversation_history)
            while True:
                try:
                    event_type, value = next(generator)
                except StopIteration as stop:
                    assistant_text, recommendations = stop.value
                    break

                if event_type == "assistant_chunk":
                    yield _sse_event({"type": "assistant_chunk", "text": value})
                elif event_type == "recommendation":
                    yield _sse_event({"type": "recommendation", "item": value})
        except Exception as exc:
            assistant_text = f"Sorry, I ran into a problem while building recommendations: {exc}"
            recommendations = []
            yield _sse_event({"type": "assistant_chunk", "text": assistant_text})

        conversation_history = _initial_conversation(payload) + [
            {
                "role": "user",
                "content": payload.message,
            },
            {
                "role": "assistant",
                "content": assistant_text,
                "recommendations": recommendations,
            },
        ]
        _finalize_interaction(db, interaction, conversation_history, assistant_text, recommendations)
        yield _sse_event({"type": "done", "conversation_history": conversation_history})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/debug")
def debug_endpoint(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    user = _resolve_user(db, authorization)
    assistant_text, recommendations = generate_recommendations(
        db,
        user,
        payload.message,
        payload.conversation_history,
    )
    return {
        "assistant_text": assistant_text,
        "recommendations": recommendations,
        "user_id": getattr(user, "id", None),
    }
