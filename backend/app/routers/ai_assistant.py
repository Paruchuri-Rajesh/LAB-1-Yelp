from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Generator
import json
from app.models.ai_interaction import AIInteraction
from app.database import get_db
from app.schemas.ai_assistant import AIChatRequest, AIChatResponse, Recommendation
from app.services.ai_agent import generate_recommendations, build_system_prompt
from app.services.user_service import get_user_by_id
from app.services.auth_service import decode_access_token

router = APIRouter()


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/chat")
def chat_endpoint(payload: AIChatRequest, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    """Stream assistant response as Server-Sent Events (SSE).

    Events are JSON objects with a `type` field. Types:
      - start: initial metadata
      - assistant_chunk: piece of assistant text
      - recommendation: a single recommendation object
      - done: final event with conversation_history
    """
    # Try to load user from Authorization header if present (Bearer token)
    user = None
    if authorization:
        try:
            token = authorization.split(" ")[1]
            user_id = decode_access_token(token)
            user = get_user_by_id(db, user_id)
        except Exception:
            # silently ignore auth issues and proceed as anonymous
            user = None

    def event_stream() -> Generator[str, None, None]:
        # Persist incoming interaction (status: pending)
        # Ensure there is at least the user's latest message in conversation_history so we don't lose context
        initial_conv = payload.conversation_history or []
        if not initial_conv:
            initial_conv = [{"role": "user", "content": payload.message}]

        ai_rec = AIInteraction(
            user_id=user.id if user else None,
            query=payload.message,
            conversation_history=initial_conv,
            assistant_text=None,
            recommendations=None,
            meta={"status": "pending"},
        )
        db.add(ai_rec)
        db.flush()

        # Indicate whether external services will be used (client can show status)
        from app.config import settings as _settings
        start_meta = {"message": "stream_start", "uses_ollama": bool(_settings.OLLAMA_URL and _settings.OLLAMA_MODEL), "uses_tavily": bool(_settings.TAVILY_URL)}

        # Start event (sent before heavy processing so client can update UI)
        yield _sse_event({"type": "start", **start_meta})

        # If the client asked for an empty message (e.g., initial open), return a friendly greeting
        msg_text = (payload.message or "").strip()
        if not msg_text:
            # personalize greeting if possible
            name = None
            try:
                if user:
                    name = getattr(user, "name", None) or getattr(user, "username", None)
            except Exception:
                name = None
            greet = f"Hi {name}!" if name else "Hi there!"
            greet += " I'm your assistant — ask me for restaurant recommendations or say 'help' to get started."

            # persist greeting immediately and return
            try:
                ai_rec.assistant_text = greet
                conv = (payload.conversation_history or initial_conv) + [{"role": "assistant", "content": greet}]
                ai_rec.conversation_history = conv
                ai_rec.meta = {"status": "done", "summary": greet[:200], "recommendation_count": 0}
                db.add(ai_rec)
                db.commit()
            except Exception:
                db.rollback()

            yield _sse_event({"type": "assistant_chunk", "text": greet})
            yield _sse_event({"type": "done", "conversation_history": ai_rec.conversation_history})
            return

        # If Ollama is configured, prefer streaming path so client gets token-level updates
        from app.config import settings as _settings
        if _settings.OLLAMA_URL and _settings.OLLAMA_MODEL:
            # stream_recommendations yields tuples like ("assistant_chunk", text) and ("recommendation", rec)
            from app.services.ai_agent import stream_recommendations

            stream_gen = stream_recommendations(db, user, payload.message, payload.conversation_history)
            # stream_gen is a generator; iterate using next() so we can capture its return value
            final_summary = None
            final_recommendations = []
            assistant_buf_parts: list = []
            chunk_count = 0
            iterator = iter(stream_gen)
            while True:
                try:
                    item = next(iterator)
                except StopIteration as ret:
                    # generator returned (assistant_summary, recommendations)
                    try:
                        final_summary, final_recommendations = ret.value
                    except Exception:
                        final_summary, final_recommendations = None, []
                    break
                except Exception:
                    # unexpected exception while iterating the generator
                    final_summary, final_recommendations = None, []
                    break

                if not item:
                    continue
                typ, val = item
                if typ == "assistant_chunk":
                    # stream chunk to client
                    yield _sse_event({"type": "assistant_chunk", "text": val})
                    # append to in-memory buffer and persist every N chunks so session history is durable
                    try:
                        assistant_buf_parts.append(val)
                        chunk_count += 1
                        if chunk_count % 5 == 0:
                            ai_rec.assistant_text = "".join(assistant_buf_parts)
                            ai_rec.meta = {**(ai_rec.meta or {}), "status": "streaming"}
                            try:
                                db.add(ai_rec)
                                db.commit()
                            except Exception:
                                db.rollback()
                    except Exception:
                        pass
                elif typ == "recommendation":
                    yield _sse_event({"type": "recommendation", "item": val})
                else:
                    # unknown tuple, ignore
                    pass

            # If stream didn't return final summary, run a non-stream generation to obtain it
            if final_summary is None:
                try:
                    assistant_text, recommendations = generate_recommendations(db, user, payload.message, payload.conversation_history)
                    # We already streamed assistant chunks, but ensure recommendations are streamed
                    for rec in recommendations or []:
                        yield _sse_event({"type": "recommendation", "item": rec})
                    final_summary = assistant_text
                    final_recommendations = recommendations
                except Exception:
                    final_summary, final_recommendations = None, []

            # finalize conversation history: start from whatever was provided (or initial conv) and append assistant final
            conv = (payload.conversation_history or initial_conv) + [{"role": "assistant", "content": final_summary}]

            # persist final results and a short session summary into meta
            try:
                # ensure assistant_text contains the full assembled text (from buffer or final_summary)
                full_assistant_text = "".join(assistant_buf_parts) if assistant_buf_parts else (final_summary or "")
                ai_rec.assistant_text = full_assistant_text
                ai_rec.recommendations = final_recommendations
                ai_rec.conversation_history = conv
                # store a short session summary and mark done; include any meta the agent may want
                meta = {"status": "done", "summary": (final_summary or full_assistant_text or "")[:200]}
                try:
                    meta["recommendation_count"] = len(final_recommendations or [])
                except Exception:
                    pass
                ai_rec.meta = meta
                db.add(ai_rec)
                db.commit()
            except Exception:
                db.rollback()

            yield _sse_event({"type": "done", "conversation_history": conv})
            return
        else:
            assistant_text, recommendations = generate_recommendations(db, user, payload.message, payload.conversation_history)

            # Stream assistant_text in small chunks so UI can render progressively
            if assistant_text:
                # split into sentence-ish chunks, fallback to 200-char chunks
                import re
                parts = re.split(r"(\.[ \n])", assistant_text)
                if not parts:
                    parts = [assistant_text]
                # recombine safe chunks
                chunks = []
                buf = ""
                for p in parts:
                    if len(buf) + len(p) > 300:
                        if buf:
                            chunks.append(buf)
                        buf = p
                    else:
                        buf += p
                if buf:
                    chunks.append(buf)

                for chunk in chunks:
                    yield _sse_event({"type": "assistant_chunk", "text": chunk})

        # Stream recommendations one by one
        for rec in recommendations or []:
            yield _sse_event({"type": "recommendation", "item": rec})

        conv = (payload.conversation_history or []) + [{"role": "assistant", "content": assistant_text}]

        # Update persisted AIInteraction with results
        try:
            ai_rec.assistant_text = assistant_text
            ai_rec.recommendations = recommendations
            ai_rec.conversation_history = conv
            # store a short session summary and mark done; include any meta the agent may want
            meta = {"status": "done", "summary": (assistant_text or "")[:200]}
            # if recommendations are present, include a small count
            try:
                meta["recommendation_count"] = len(recommendations or [])
            except Exception:
                pass
            ai_rec.meta = meta
            db.commit()
        except Exception:
            db.rollback()

        yield _sse_event({"type": "done", "conversation_history": conv})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/json", response_model=AIChatResponse)
def chat_json_endpoint(payload: AIChatRequest, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    """Non-streaming JSON endpoint kept for backward compatibility with clients that expect a single JSON response.

    This will also persist the interaction to `ai_interactions` like the streaming endpoint.
    """
    # Try to load user from Authorization header if present (Bearer token)
    user = None
    if authorization:
        try:
            token = authorization.split(" ")[1]
            user_id = decode_access_token(token)
            user = get_user_by_id(db, user_id)
        except Exception:
            user = None

    # Persist incoming interaction
    # initialize conversation_history and handle empty-message greeting
    initial_conv = payload.conversation_history or []
    if not initial_conv:
        initial_conv = [{"role": "user", "content": payload.message}]

    ai_rec = AIInteraction(
        user_id=user.id if user else None,
        query=payload.message,
        conversation_history=initial_conv,
        assistant_text=None,
        recommendations=None,
        meta={"status": "pending"},
    )
    db.add(ai_rec)
    db.flush()

    # quick greeting path when message is empty
    if not (payload.message or "").strip():
        name = None
        try:
            if user:
                name = getattr(user, "name", None) or getattr(user, "username", None)
        except Exception:
            name = None
        greet = f"Hi {name}!" if name else "Hi there!"
        greet += " I'm your assistant — ask me for restaurant recommendations or say 'help' to get started."
        conv = initial_conv + [{"role": "assistant", "content": greet}]
        try:
            ai_rec.assistant_text = greet
            ai_rec.conversation_history = conv
            ai_rec.meta = {"status": "done", "summary": greet[:200], "recommendation_count": 0}
            db.add(ai_rec)
            db.commit()
        except Exception:
            db.rollback()

        return {"assistant_text": greet, "recommendations": [], "conversation_history": conv}

    assistant_text, recommendations = generate_recommendations(db, user, payload.message, payload.conversation_history)

    conv = (payload.conversation_history or []) + [{"role": "assistant", "content": assistant_text}]

    try:
        ai_rec.assistant_text = assistant_text
        ai_rec.recommendations = recommendations
        ai_rec.conversation_history = conv
        meta = {"status": "done", "summary": (assistant_text or "")[:200]}
        try:
            meta["recommendation_count"] = len(recommendations or [])
        except Exception:
            pass
        ai_rec.meta = meta
        db.commit()
    except Exception:
        db.rollback()

    return {
        "assistant_text": assistant_text,
        "recommendations": recommendations,
        "conversation_history": conv,
    }


@router.post("/debug")
def debug_endpoint(payload: AIChatRequest, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    """Developer debug endpoint: calls Tavily search + extract and (optionally) Ollama and returns raw results.

    This endpoint is intended for debugging and prompt tuning. It uses TAVILY_URL and TAVILY_API_KEY from .env.
    """
    # load user if provided
    user = None
    if authorization:
        try:
            token = authorization.split(" ")[1]
            user_id = decode_access_token(token)
            user = get_user_by_id(db, user_id)
        except Exception:
            user = None

    out = {"hits": None, "extract": None, "ollama": None, "errors": []}
    try:
        from app.config import settings as _settings
        from app.services.ai_agent_tavily import search as tavily_search
        hits = tavily_search(payload.message, limit=5)
        out["hits"] = hits
        if hits and isinstance(hits, list) and hits[0].get("url"):
            try:
                from app.services.ai_agent_tavily import extract as tavily_extract
                extracted = tavily_extract(hits[0]["url"])
                out["extract"] = extracted
                # If Ollama configured, call it to condense
                if _settings.OLLAMA_URL and _settings.OLLAMA_MODEL:
                    try:
                        from app.services.ai_agent_ollama import call_ollama
                        # build compact prefs summary for system prompt
                        prefs = {"cuisine_preferences": []}
                        try:
                            if user and getattr(user, "id", None):
                                p = getattr(user, "preferences", None)
                                if p:
                                    prefs["cuisine_preferences"] = p.cuisine_preferences or []
                                    prefs["price_range"] = getattr(p, "price_range", None)
                                    prefs["dietary"] = p.dietary_restrictions or []
                        except Exception:
                            prefs["cuisine_preferences"] = []

                        system_pref = build_system_prompt(user, prefs)
                        print(f"System Pref {system_pref}")
                        prompt = f"{system_pref}\nQuestion: {payload.message}\n\nContent:\n{extracted.get('content') or extracted.get('text') or ''}"
                        print(prompt)
                        text = call_ollama(prompt)
                        out["ollama"] = text
                    except Exception as e:
                        out["errors"].append(str(e))
            except Exception as e:
                out["errors"].append(str(e))
    except Exception as e:
        out["errors"].append(str(e))

    return out
