from typing import Any, Dict, List, Optional, Tuple
from app.services import restaurant_service, review_service
from app.database import get_db
from sqlalchemy.orm import Session
import re
import json
from app.services.user_service import get_user_by_id
import logging

logger = logging.getLogger(__name__)


def _simple_extract(message: str) -> Dict[str, Optional[str]]:
    """Very small rule-based extractor for cuisine, price, dietary, and occasion."""
    out = {"cuisine": None, "price_range": None, "dietary": None, "occasion": None, "location": None}
    msg = message.lower()
    # cuisine (common list)
    cuisines = ["italian", "french", "japanese", "sushi", "vegan", "thai", "mexican", "indian", "chinese"]
    for c in cuisines:
        if c in msg:
            out["cuisine"] = c if c != "sushi" else "japanese"
            break

    # price signs
    if "$" in message:
        # map $$ -> $$ etc by counting
        dollars = message.count("$")
        out["price_range"] = "$" * min(max(dollars, 1), 3)
    else:
        if "cheap" in msg or "affordable" in msg or "casual" in msg:
            out["price_range"] = "$"
        if "mid" in msg or "moderate" in msg or "mid-range" in msg:
            out["price_range"] = "$$"
        if "expensive" in msg or "romantic" in msg or "special" in msg:
            out["price_range"] = "$$$"

    # dietary
    if "vegan" in msg:
        out["dietary"] = "vegan"
    elif "vegetarian" in msg:
        out["dietary"] = "vegetarian"

    # occasion
    if "anniversary" in msg or "romantic" in msg or "date" in msg:
        out["occasion"] = "romantic"
    if "dinner" in msg:
        out["occasion"] = out.get("occasion") or "dinner"

    # location (improved: look for 'near <place>' or 'in <city>' anywhere)
    m = re.search(r"(?:near|in) ([A-Za-z\s]+?)(?:\b|$)", message, re.IGNORECASE)
    if m:
        loc = m.group(1).strip()
        # strip trailing stop words
        loc = re.sub(r"\b(please|thanks|thanks\b).*$", "", loc, flags=re.IGNORECASE).strip()
        out["location"] = loc

    return out


def _restaurant_to_recommendation(r) -> Dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "avg_rating": float(r.avg_rating or 0),
        "review_count": int(r.review_count or 0),
        "price_range": r.price_range,
        "cuisine_type": r.cuisine_type,
    }


def build_system_prompt(user: Optional[Any], prefs: Dict[str, Any]) -> str:
    """Return a short system prompt fragment that summarizes user identity and preferences.

    This is intentionally compact to avoid token bloat when prepending to streaming prompts.
    """
    parts: List[str] = ["You are an assistant personalized to the requesting user."]
    try:
        if user and getattr(user, "id", None):
            uname = getattr(user, "name", None) or getattr(user, "username", None) or ""
            parts.append(f"UserID: {getattr(user, 'id')} name: {uname}")
    except Exception:
        pass

    try:
        if prefs:
            if prefs.get("cuisine_preferences"):
                parts.append(f"Saved cuisine preferences: {prefs.get('cuisine_preferences')}")
            if prefs.get("price_range"):
                parts.append(f"Saved price_range: {prefs.get('price_range')}")
            if prefs.get("dietary"):
                parts.append(f"Saved dietary: {prefs.get('dietary')}")
    except Exception:
        pass

    return "\n".join(parts)


def generate_recommendations(db: Session, user: Optional[Any], message: str, conversation_history: Optional[List[Any]] = None, limit: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
    # 1) Load user preferences from DB (ensure we have fresh object attached to session)
    prefs: Dict[str, Any] = {"cuisine_preferences": []}
    try:
        if user and getattr(user, "id", None):
            user = get_user_by_id(db, int(user.id)) or user
            p = getattr(user, "preferences", None)
            if p:
                prefs["cuisine_preferences"] = p.cuisine_preferences or []
                prefs["price_range"] = getattr(p, "price_range", None)
                prefs["dietary"] = p.dietary_restrictions or []
            else:
                prefs["cuisine_preferences"] = []
    except Exception:
        prefs["cuisine_preferences"] = []

    # Quick heuristic: if the user is asking a factual lookup (calories, "how many", "what is" etc.)
    # prefer to use Tavily search/extract to fetch factual content and answer directly.
    fact_q = False
    if re.search(r"\b(calorie|calories|how many|what is|who is|when|where|define|definition)\b", message, re.IGNORECASE):
        fact_q = True

    if fact_q:
        # Try Tavily first for factual content
        try:
            from app.config import settings as _settings
            if _settings.TAVILY_URL:
                from app.services.ai_agent_tavily import search as tavily_search
                hits = tavily_search(message, limit=3)
                try:
                    # print to console so developers see Tavily hits and why model needn't ask for prefs
                    logger.info("ai_agent.fact_q tavily hits (truncated): %s", str(hits)[:1000])
                except Exception:
                    pass
                # If hits have snippets, assemble a concise factual answer
                if hits:
                    # pick best snippet
                    best = hits[0]
                    snippet = (best.get("snippet") or "").strip()
                    url = best.get("url") or ""

                    # Try to extract the full article/content using Tavily Extract when a URL is available
                    full_text = None
                    try:
                        if url:
                            from app.services.ai_agent_tavily import extract as tavily_extract
                            extracted = tavily_extract(url)
                            full_text = extracted.get("content") or extracted.get("text") or None
                            try:
                                logger.info("ai_agent.fact_q tavily extracted content length: %d", len(full_text or ""))
                            except Exception:
                                pass
                    except Exception:
                        full_text = None

                    # Build a combined text to synthesize from
                    combined = "\n".join([t for t in [snippet, full_text] if t])

                    # If Ollama available, ask it to synthesize a concise, fully-analyzed answer
                    try:
                        if _settings.OLLAMA_URL and _settings.OLLAMA_MODEL:
                            from app.services.ai_agent_ollama import call_ollama
                            # prepend a compact system prompt containing user prefs
                            system_pref = build_system_prompt(user, prefs)
                            prompt = (
                                f"{system_pref}\nYou are an expert assistant. Answer the question using the provided web content, and cite the source URL when appropriate."
                                f"\nQuestion: {message}\n\nContent:\n{combined}\n\nProvide a concise factual answer (1-3 sentences) and include the source URL at the end in parentheses."
                            )
                            condensed = call_ollama(prompt, max_tokens=300)
                            if condensed and isinstance(condensed, str) and condensed.strip():
                                return condensed.strip(), []
                    except Exception:
                        pass

                    # Fallback local summarization: try to find numeric or calorie info in combined text
                    if combined:
                        # look for calorie mentions like '123 kcal' or '123 calories'
                        m = re.search(r"(\d{2,5})\s*(kcal|calories|cal)", combined, re.IGNORECASE)
                        if m:
                            return f"About {m.group(1)} calories (source: {url})", []

                        # Otherwise, attempt to return the first 2 sentences from combined
                        sentences = re.split(r"(?<=[.!?])\s+", combined.strip())
                        if sentences:
                            answer = " ".join(sentences[:2])
                            if url:
                                answer = f"{answer} (source: {url})"
                            return answer, []

                    # Last resort: return the snippet or URL
                    answer = snippet or f"I found a source: {url}"
                    return answer, []
        except Exception:
            # fall through to normal processing if Tavily fails
            pass

    # 2) Interpret query
    # Detect whether the user is explicitly asking for recommendations
    def _is_recommendation_query(text: str) -> bool:
        if not text:
            return False
        # broaden detection keywords and allow plural/synonyms and fuzzy mentions like 'vegetarian', 'vegan', 'restaurants'
        keywords = [
            r"recommend", r"suggest", r"find", r"best", r"nearby", r"near me", r"where to",
            r"places to", r"restaurants?", r"eat", r"dine", r"vegan", r"vegetarian",
            r"veggie", r"food options", r"places", r"dinner", r"lunch",
        ]
        pattern = r"\b(?:" + r"|".join(keywords) + r")\b"
        return bool(re.search(pattern, text, re.IGNORECASE))

    rec_query = _is_recommendation_query(message)

    # If this isn't a recommendation query, avoid returning DB recommendation cards; just synthesize an assistant response.
    if not rec_query and fact_q is False:
        # fallback simple assistant text using Tavily or rule-based extractor
        try:
            # If we have Tavily and Ollama, synthesize a helpful assistant reply without recommending.
            from app.config import settings as _settings
            if _settings.TAVILY_URL:
                from app.services.ai_agent_tavily import search as tavily_search
                hits = tavily_search(message, limit=3)
                snippet = hits[0].get("snippet") if hits and isinstance(hits, list) and hits[0] else None
                if snippet:
                    # if Ollama is available, condense
                    try:
                        if _settings.OLLAMA_URL and _settings.OLLAMA_MODEL:
                            from app.services.ai_agent_ollama import call_ollama
                            # include compact system prompt summary so model sees user prefs
                            system_pref = build_system_prompt(user, prefs)
                            prompt = f"{system_pref}\nYou are an assistant. Answer succinctly: {message}\n\nContext: {snippet}\n"
                            condensed = call_ollama(prompt, max_tokens=200)
                            if condensed:
                                return condensed.strip(), []
                    except Exception:
                        return snippet, []
        except Exception:
            pass
        # default reply
        return ("I can help with that — tell me if you'd like restaurant recommendations or more details."), []
    # Flow:
    #  - If Tavily is configured, call it to obtain web search results.
    #  - Prefer Ollama for extraction/synthesis if configured and pass web results in the prompt.
    #  - Otherwise try LangChain/OpenAI if available, then fall back to the simple rule-based extractor.
    extracted = None
    try:
        from app.config import settings as _settings
        web_results = None
        # Try Tavily first to gather web results
        try:
                if _settings.TAVILY_URL:
                    from app.services.ai_agent_tavily import search as tavily_search
                    web_results = tavily_search(message, limit=6)
                    try:
                        logger.info("ai_agent.web_results count: %d", len(web_results or []))
                    except Exception:
                        pass
        except Exception:
            web_results = None

            # If Ollama is available, synthesize/extract using Ollama and include web_results (when present)
            if _settings.OLLAMA_URL and _settings.OLLAMA_MODEL:
                from app.services.ai_agent_ollama import call_ollama

                # Gather some user history (recent reviews) to give the model context about likes/dislikes
                user_history_text = ""
                try:
                    if user and getattr(user, "id", None):
                        reviews, _ = review_service.get_user_reviews(db, user.id, page=1, page_size=10)
                        if reviews:
                            # compact representation of what the user liked/disliked
                            hist_lines: List[str] = []
                            for rv in reviews:
                                score = getattr(rv, "rating", None) or getattr(rv, "rating_value", None) or getattr(rv, "score", None) or None
                                author_note = getattr(rv, "body", None) or getattr(rv, "text", None) or getattr(rv, "content", None) or getattr(rv, "review_text", None) or None
                                hist_lines.append(f"{rv.business_id}: rating={score} text={ (author_note or '')[:200] }")
                            user_history_text = "\n".join(hist_lines)
                except Exception:
                    user_history_text = ""

                # Build a compact prompt that includes the user message, preferences, and a short digest of web results and user history
                # Provide a compact schema description so the model can suggest DB filters / SQL-like queries
                schema_desc = (
                    "Restaurant schema fields: id (int), name (text), avg_rating (float), review_count (int), "
                    "price_range (string: $, $$, $$$), cuisine_type (string), address (text), city (string), state (string), zip_code (string)."
                )

                prompt = (
                    f"You are an assistant that helps suggest restaurants and dishes. "
                    f"Available DB schema: {schema_desc}\n"
                    f"Extract filters (cuisine, price_range, dietary, occasion, location) from the user query: {message}\n"
                )
                if prefs.get("cuisine_preferences"):
                    prompt += f"User saved cuisine preferences: {prefs.get('cuisine_preferences')}\n"
                if user_history_text:
                    prompt += f"User recent reviews and history (id:rating:text):\n{user_history_text}\n"

                if web_results:
                    prompt += "\nWeb search results:\n"
                    for i, hit in enumerate(web_results[:6], start=1):
                        title = hit.get("title") or ""
                        url = hit.get("url") or ""
                        snippet = (hit.get("snippet") or "").strip().replace("\n", " ")
                        prompt += f"{i}. {title} - {url} - {snippet}\n"

                # Allow the model to request a tool call by returning a line that begins with TOOL_CALL: followed by a JSON payload
                prompt += (
                    "\nIf you need database information, emit a single line starting with 'TOOL_CALL:' followed by a JSON object like:"
                    " {'tool':'search_restaurants','args':{'cuisine':'italian','limit':5}} and wait for the tool result."
                )

                # iterative tool call handling loop: model may request tools; we execute and feed results back up to 3 iterations
                tool_loop = 0
                model_response = None
                while tool_loop < 3:
                    # ensure system prefs are visible to the model in synchronous calls too
                    system_pref = build_system_prompt(user, prefs)
                    # include a firm instruction to NOT ask the user for preferences; they are loaded from DB
                    insist = f"\nIMPORTANT: Do NOT ask the user for preferences. Use the saved preferences: {prefs}. If none, proceed without asking."
                    model_response = call_ollama(f"{system_pref}\n{prompt}{insist}")
                    try:
                        logger.info("ai_agent.tool_loop model_response (truncated): %s", (model_response or '')[:1000])
                    except Exception:
                        pass
                    if not model_response:
                        break
                    # detect a tool call
                    tc = None
                    for line in (model_response or "").splitlines():
                        if line.strip().startswith("TOOL_CALL:"):
                            try:
                                payload = line.strip()[len("TOOL_CALL:"):].strip()
                                tc = json.loads(payload)
                                break
                            except Exception:
                                tc = None
                                break

                    if not tc:
                        # no tool call requested; use this model_response as final output
                        text = model_response
                        break

                    # execute the requested tool
                    tool_name = tc.get("tool")
                    tool_args = tc.get("args", {}) or {}
                    tool_result_text = ""
                    try:
                        if tool_name == "search_restaurants":
                            q = tool_args.get("q") or message
                            cuisine = tool_args.get("cuisine")
                            location = tool_args.get("location")
                            price_range = tool_args.get("price_range")
                            page = int(tool_args.get("page", 1))
                            page_size = int(tool_args.get("limit", 10))
                            items, total = restaurant_service.search_restaurants(db, q=q, cuisine=cuisine, location=location, price_range=price_range, page=page, page_size=page_size)
                            # compact JSON-serializable summary
                            tool_result_text = json.dumps([_restaurant_to_recommendation(r) for r in items[:page_size]])
                            try:
                                logger.info("ai_agent.tool_result search_restaurants returned %d items", len(items))
                            except Exception:
                                pass
                        elif tool_name == "get_user_reviews":
                            uid = tool_args.get("user_id") or (user.id if user else None)
                            if uid:
                                revs, total = review_service.get_user_reviews(db, int(uid), page=1, page_size=10)
                                tool_result_text = json.dumps([{"business_id": r.business_id, "rating": getattr(r, 'rating', None) or getattr(r, 'rating_value', None) or None, "text": (getattr(r, 'body', None) or getattr(r, 'text', None) or '')[:400]} for r in revs])
                                try:
                                    logger.info("ai_agent.tool_result get_user_reviews count: %d", len(revs))
                                except Exception:
                                    pass
                            else:
                                tool_result_text = json.dumps([])
                        else:
                            tool_result_text = json.dumps({"error": "unknown tool"})
                    except Exception as e:
                        tool_result_text = json.dumps({"error": str(e)})

                    # append tool result to the prompt and loop so the model can synthesize using tool output
                    prompt += f"\nTool result for {tool_name}: {tool_result_text}\n"
                    tool_loop += 1

                # if model_response wasn't set above for some reason, set it from last call
                if model_response and not extracted:
                    text = model_response

                # small parse: look for lines like 'cuisine: italian' or 'cuisine = italian'
                extracted = {}
                for part in ["cuisine", "price_range", "dietary", "occasion", "location"]:
                    m = re.search(fr"{part}[:=]\s*([\w\s$-]+)", (text or ""), re.IGNORECASE)
                    extracted[part] = m.group(1).strip() if m else None
    except Exception:
        extracted = None

    # If not extracted yet, try LangChain/OpenAI if available, otherwise use rule-based extractor
    if not extracted:
        try:
            from langchain import LLMChain  # type: ignore
            from langchain.llms import OpenAI  # type: ignore
            # Not calling LLM here automatically in typical dev envs; fall back to rule-based
            extracted = _simple_extract(message)
        except Exception:
            extracted = _simple_extract(message)

    cuisine = extracted.get("cuisine")
    price_range = extracted.get("price_range")
    dietary = extracted.get("dietary")
    location = extracted.get("location")

    # 3) Query DB using restaurant_service
    # Use q=message as fallback search text
    items, total = restaurant_service.search_restaurants(db, q=message, cuisine=cuisine, location=location, price_range=price_range, page=1, page_size=50)

    # 4) Rank results by simple scoring: rating + preference match
    def score(r):
        s = float(r.avg_rating or 0) * 10
        # bonus if cuisine matches user prefs or extracted cuisine
        if cuisine and r.cuisine_type and cuisine.lower() in (r.cuisine_type or "").lower():
            s += 5
        for pref in prefs.get("cuisine_preferences", []):
            if pref and r.cuisine_type and pref.lower() in (r.cuisine_type or "").lower():
                s += 3
        # price match
        if price_range and r.price_range == price_range:
            s += 2
        # dietary: if vegan requested and cuisine mentions vegan or 'vegan_friendly' flag, boost (best-effort)
        return s

    scored = sorted(items, key=score, reverse=True)
    top = scored[:limit]

    recommendations = []
    reasons = []
    for r in top:
        rec = _restaurant_to_recommendation(r)
        # reason generation: small template
        reason_parts = []
        if cuisine and r.cuisine_type and cuisine.lower() in (r.cuisine_type or "").lower():
            reason_parts.append(f"Matches requested cuisine: {cuisine}")
        if prefs.get("cuisine_preferences") and any(pref.lower() in (r.cuisine_type or "").lower() for pref in prefs.get("cuisine_preferences", [])):
            reason_parts.append("Matches your saved cuisine preferences")
        if r.price_range:
            reason_parts.append(f"Price: {r.price_range}")
        rec["reason"] = "; ".join(reason_parts) or "Highly rated and matches your query"
        recommendations.append(rec)

    assistant_text = "Here are a few recommendations based on your query and preferences."
    return assistant_text, recommendations


def stream_recommendations(db: Session, user: Optional[Any], message: str, conversation_history: Optional[List[Any]] = None, limit: int = 5):
    """Generator that streams assistant text chunks (from Ollama) and yields a tuple
    ('assistant_chunk', text) for each token/chunk, then yields ('recommendation', rec) items,
    and finally returns a summary string and list of recommendations.
    """
    from app.config import settings as _settings
    from app.services.ai_agent_tavily import search as tavily_search, extract as tavily_extract
    from app.services.ai_agent_ollama import stream_ollama

    # If factual query, attempt to fetch web content first
    fact_q = False
    if re.search(r"\b(calorie|calories|how many|what is|who is|when|where|define|definition)\b", message, re.IGNORECASE):
        fact_q = True

    web_results = None
    if _settings.TAVILY_URL:
        try:
            web_results = tavily_search(message, limit=5)
        except Exception:
            web_results = None

    content_for_prompt = ""
    if fact_q and web_results and isinstance(web_results, list) and web_results and web_results[0].get("url"):
        try:
            extracted = tavily_extract(web_results[0]["url"])
            content_for_prompt = extracted.get("content") or extracted.get("text") or ""
        except Exception:
            content_for_prompt = ""

    # Load a compact copy of user preferences so we can inject them into the system prompt for streaming calls
    prefs: Dict[str, Any] = {"cuisine_preferences": []}
    try:
        if user and getattr(user, "id", None):
            from app.services.user_service import get_user_by_id
            user = get_user_by_id(db, int(user.id)) or user
            p = getattr(user, "preferences", None)
            if p:
                prefs["cuisine_preferences"] = p.cuisine_preferences or []
                prefs["price_range"] = getattr(p, "price_range", None)
                prefs["dietary"] = p.dietary_restrictions or []
            else:
                prefs["cuisine_preferences"] = []
    except Exception:
        prefs["cuisine_preferences"] = []

    # Build a succinct prompt and prepend a compact system prompt with user prefs
    from app.services.ai_agent import build_system_prompt
    system_pref = build_system_prompt(user, prefs)
    prompt = f"{system_pref}\nYou are an assistant. Answer: {message}\n{content_for_prompt}\n"

    # Stream tokens from Ollama and yield assistant_chunk tuples
    full_text_parts: List[str] = []
    try:
        for chunk in stream_ollama(prompt):
            # normalize and yield
            text_chunk = chunk if isinstance(chunk, str) else str(chunk)
            full_text_parts.append(text_chunk)
            yield ("assistant_chunk", text_chunk)
    except Exception as e:
        # fall back to non-streaming path if streaming fails
        yield ("assistant_chunk", f"[assistant error: {e}]")

    full_text = "".join(full_text_parts)

    # After streaming assistant text, run the same recommendation logic (non-streaming) to produce recs
    # Reuse generate_recommendations' DB search/ranking: call it to get recommendations (this will call Ollama sync if configured,
    # but we've already streamed a response; however for ranking we'll rely on DB)
    try:
        assistant_summary, recommendations = generate_recommendations(db, user, message, conversation_history, limit=limit)
    except Exception:
        assistant_summary, recommendations = (full_text[:300] if full_text else ""), []

    # yield recommendations
    for rec in recommendations:
        yield ("recommendation", rec)

    # final result (not yielded as event, but return for callers that want it)
    return assistant_summary, recommendations
