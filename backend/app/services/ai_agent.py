from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services import restaurant_service
from app.services.user_service import get_user_by_id

logger = logging.getLogger(__name__)

COMMON_CUISINES = [
    "italian", "chinese", "mexican", "indian", "japanese", "thai", "french",
    "american", "mediterranean", "korean", "vietnamese", "greek", "pizza",
    "sushi", "seafood", "bbq", "burgers", "dessert", "coffee", "brunch",
]
DIETARY_TERMS = [
    "vegetarian", "vegan", "halal", "gluten-free", "gluten free", "kosher",
    "dairy-free", "dairy free", "pescatarian",
]
AMBIANCE_TERMS = [
    "casual", "fine dining", "family-friendly", "family friendly", "romantic",
    "outdoor seating", "wifi", "quiet", "lively", "cozy", "upscale", "trendy",
    "brunch", "date night", "bar", "rooftop",
]
CURRENT_CONTEXT_HINTS = re.compile(
    r"\b(open|opening|hours|hour|tonight|today|tomorrow|weekend|current|trending|special|event|events|busy|popular)\b",
    re.IGNORECASE,
)
FOLLOW_UP_HINTS = re.compile(
    r"\b(another|else|instead|same|similar|cheaper|pricier|expensive|romantic|casual|closer|nearer|more|less|what about|how about)\b",
    re.IGNORECASE,
)
SORT_MAP = {
    "rating": "rating",
    "best": "rating",
    "popular": "review_count",
    "popularity": "review_count",
    "reviews": "review_count",
    "price": "price",
    "cheapest": "price",
    "distance": "recommended",
    "nearby": "recommended",
    "recommended": "recommended",
    "newest": "newest",
}


class ExtractedQuery(BaseModel):
    cuisine: Optional[str] = None
    price_range: Optional[str] = None
    dietary: List[str] = Field(default_factory=list)
    occasion: Optional[str] = None
    ambiance: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    sort_preference: Optional[str] = None
    wants_current_context: bool = False


def _normalize_price(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = str(value).strip()
    dollars = value.count("$")
    if dollars:
        return "$" * min(max(dollars, 1), 4)
    lowered = value.lower()
    if any(term in lowered for term in ["cheap", "budget", "affordable", "low"]):
        return "$"
    if any(term in lowered for term in ["mid", "moderate", "average"]):
        return "$$"
    if any(term in lowered for term in ["expensive", "upscale", "fancy", "special"]):
        return "$$$"
    return None


def _price_rank(value: Optional[str]) -> int:
    if not value:
        return 0
    return min(value.count("$"), 4)


def _normalize_sort(value: Optional[str]) -> str:
    if not value:
        return "recommended"
    key = str(value).strip().lower()
    return SORT_MAP.get(key, "recommended")


def _clean_location(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = re.sub(r"\b(please|thanks|thank you|tonight|today|now)\b", "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
    return cleaned or None


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        text = (value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _history_messages(conversation_history: Optional[List[Any]]) -> List[Dict[str, Any]]:
    if not conversation_history:
        return []
    cleaned: List[Dict[str, Any]] = []
    for item in conversation_history:
        if isinstance(item, dict):
            cleaned.append(item)
    return cleaned


def _history_has_recommendations(conversation_history: Optional[List[Any]]) -> bool:
    for item in _history_messages(conversation_history):
        recs = item.get("recommendations")
        if isinstance(recs, list) and recs:
            return True
    return False


def _build_history_summary(conversation_history: Optional[List[Any]], limit: int = 6) -> str:
    snippets: List[str] = []
    for item in _history_messages(conversation_history)[-limit:]:
        role = item.get("role") or "user"
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        snippets.append(f"{role}: {content[:220]}")
    return "\n".join(snippets)


def _simple_extract(message: str) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = text.lower()
    extracted: Dict[str, Any] = {
        "cuisine": None,
        "price_range": _normalize_price(text),
        "dietary": [],
        "occasion": None,
        "ambiance": [],
        "location": None,
        "keywords": [],
        "sort_preference": None,
        "wants_current_context": bool(CURRENT_CONTEXT_HINTS.search(text)),
    }

    for cuisine in COMMON_CUISINES:
        if re.search(rf"\b{re.escape(cuisine)}\b", lowered):
            extracted["cuisine"] = "japanese" if cuisine == "sushi" else cuisine
            break

    if not extracted["price_range"]:
        if any(word in lowered for word in ["cheap", "budget", "affordable"]):
            extracted["price_range"] = "$"
        elif any(word in lowered for word in ["mid-range", "mid range", "moderate"]):
            extracted["price_range"] = "$$"
        elif any(word in lowered for word in ["expensive", "fancy", "upscale"]):
            extracted["price_range"] = "$$$"

    for term in DIETARY_TERMS:
        if term in lowered:
            normalized = term.replace(" ", "-")
            extracted["dietary"].append(normalized)

    if any(word in lowered for word in ["anniversary", "date", "romantic"]):
        extracted["occasion"] = "romantic"
    elif "dinner" in lowered:
        extracted["occasion"] = "dinner"
    elif "lunch" in lowered:
        extracted["occasion"] = "lunch"
    elif "brunch" in lowered:
        extracted["occasion"] = "brunch"

    for term in AMBIANCE_TERMS:
        if term in lowered:
            extracted["ambiance"].append(term.replace(" ", "-"))

    loc_match = re.search(
        r"(?:near|in|around|at)\s+([A-Za-z][A-Za-z\s,.-]{1,60})(?:$|\b(?:with|for|that|which|under|around|and)\b)",
        text,
        re.IGNORECASE,
    )
    if loc_match:
        extracted["location"] = _clean_location(loc_match.group(1))

    if re.search(r"\b(best rated|highest rated|top rated)\b", lowered):
        extracted["sort_preference"] = "rating"
    elif re.search(r"\b(popular|most popular|trending)\b", lowered):
        extracted["sort_preference"] = "review_count"
    elif re.search(r"\b(cheapest|lowest price)\b", lowered):
        extracted["sort_preference"] = "price"

    keyword_hits: List[str] = []
    for word in ["wifi", "quiet", "patio", "outdoor", "family", "romantic", "vegan", "vegetarian", "delivery", "takeout"]:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            keyword_hits.append(word)
    if extracted["occasion"]:
        keyword_hits.append(extracted["occasion"])
    extracted["keywords"] = _dedupe(keyword_hits)
    extracted["dietary"] = _dedupe(extracted["dietary"])
    extracted["ambiance"] = _dedupe(extracted["ambiance"])
    return extracted


def _extract_with_langchain(
    message: str,
    conversation_history: Optional[List[Any]],
    preferences: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    try:
        from langchain.output_parsers import PydanticOutputParser
        from langchain.prompts import PromptTemplate
        from app.config import settings
        from app.services.ai_agent_ollama import call_ollama
    except Exception:
        return None

    if not settings.OLLAMA_URL or not settings.OLLAMA_MODEL:
        return None

    parser = PydanticOutputParser(pydantic_object=ExtractedQuery)
    prompt = PromptTemplate(
        template=(
            "You extract restaurant recommendation filters from user messages.\n"
            "Saved preferences: {preferences}\n"
            "Conversation history:\n{history}\n\n"
            "Latest user message: {message}\n\n"
            "Return only valid JSON matching these instructions:\n{format_instructions}\n"
            "Use null for unknown scalar values and [] for unknown list values.\n"
            "Infer follow-up requests from conversation history.\n"
            "Set wants_current_context=true for questions about current hours, events, tonight, today, or trending places."
        ),
        input_variables=["preferences", "history", "message"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    try:
        rendered = prompt.format(
            preferences=json.dumps(preferences, ensure_ascii=False),
            history=_build_history_summary(conversation_history),
            message=message,
        )
        raw = call_ollama(rendered, max_tokens=400, temperature=0.0)
        cleaned = str(raw or "").strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
        if fence_match:
            cleaned = fence_match.group(1)
        parsed = parser.parse(cleaned)
        data = parsed.model_dump()
        data["price_range"] = _normalize_price(data.get("price_range"))
        data["location"] = _clean_location(data.get("location"))
        data["sort_preference"] = _normalize_sort(data.get("sort_preference"))
        data["dietary"] = _dedupe([str(item).lower() for item in data.get("dietary", [])])
        data["ambiance"] = _dedupe([str(item).lower() for item in data.get("ambiance", [])])
        data["keywords"] = _dedupe([str(item).lower() for item in data.get("keywords", [])])
        return data
    except Exception as exc:
        logger.debug("LangChain extraction failed: %s", exc)
        return None


def _load_user_preferences(db: Session, user: Optional[Any]) -> Dict[str, Any]:
    preferences: Dict[str, Any] = {
        "cuisine_preferences": [],
        "price_range": None,
        "dietary_restrictions": [],
        "ambiance_preferences": [],
        "preferred_locations": [],
        "sort_preference": "rating",
        "search_radius_miles": 10,
    }
    try:
        if user and getattr(user, "id", None):
            user = get_user_by_id(db, int(user.id)) or user
            pref = getattr(user, "preferences", None)
            if pref:
                preferences["cuisine_preferences"] = pref.cuisine_preferences or []
                preferences["price_range"] = getattr(pref, "price_range", None)
                preferences["dietary_restrictions"] = pref.dietary_restrictions or []
                preferences["ambiance_preferences"] = pref.ambiance_preferences or []
                preferences["preferred_locations"] = pref.preferred_locations or []
                preferences["sort_preference"] = getattr(pref, "sort_preference", None) or "rating"
                preferences["search_radius_miles"] = getattr(pref, "search_radius_miles", 10) or 10
    except Exception as exc:
        logger.debug("Failed to load user preferences: %s", exc)
    return preferences


def _merge_filters(
    message: str,
    extracted: Dict[str, Any],
    conversation_history: Optional[List[Any]],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    resolved = dict(extracted)
    history_filters: List[Dict[str, Any]] = []
    for item in _history_messages(conversation_history):
        if item.get("role") != "user":
            continue
        content = str(item.get("content") or "").strip()
        if content:
            history_filters.append(_simple_extract(content))

    for hist in history_filters:
        if not resolved.get("cuisine") and hist.get("cuisine"):
            resolved["cuisine"] = hist["cuisine"]
        if not resolved.get("location") and hist.get("location"):
            resolved["location"] = hist["location"]
        if not resolved.get("occasion") and hist.get("occasion"):
            resolved["occasion"] = hist["occasion"]
        if not resolved.get("price_range") and hist.get("price_range"):
            resolved["price_range"] = hist["price_range"]
        resolved["dietary"] = _dedupe((hist.get("dietary") or []) + (resolved.get("dietary") or []))
        resolved["ambiance"] = _dedupe((hist.get("ambiance") or []) + (resolved.get("ambiance") or []))
        resolved["keywords"] = _dedupe((hist.get("keywords") or []) + (resolved.get("keywords") or []))
        if not resolved.get("sort_preference") and hist.get("sort_preference"):
            resolved["sort_preference"] = hist["sort_preference"]
        resolved["wants_current_context"] = bool(resolved.get("wants_current_context") or hist.get("wants_current_context"))

    lowered = (message or "").lower()
    base_price = resolved.get("price_range") or preferences.get("price_range")
    if "cheaper" in lowered or "less expensive" in lowered:
        rank = max(_price_rank(base_price) - 1, 1)
        resolved["price_range"] = "$" * rank
        resolved["sort_preference"] = "price"
    elif any(word in lowered for word in ["fancier", "nicer", "more expensive", "upscale"]):
        rank = min(max(_price_rank(base_price), 1) + 1, 4)
        resolved["price_range"] = "$" * rank

    if not resolved.get("cuisine") and preferences.get("cuisine_preferences"):
        resolved["cuisine"] = preferences["cuisine_preferences"][0]
    if not resolved.get("price_range") and preferences.get("price_range"):
        resolved["price_range"] = str(preferences["price_range"])
    if not resolved.get("location") and preferences.get("preferred_locations"):
        resolved["location"] = preferences["preferred_locations"][0]
    if not resolved.get("sort_preference") and preferences.get("sort_preference"):
        resolved["sort_preference"] = str(preferences["sort_preference"])
    resolved["dietary"] = _dedupe((resolved.get("dietary") or []) + (preferences.get("dietary_restrictions") or []))
    resolved["ambiance"] = _dedupe((resolved.get("ambiance") or []) + (preferences.get("ambiance_preferences") or []))
    resolved["sort_preference"] = _normalize_sort(resolved.get("sort_preference"))
    resolved["price_range"] = _normalize_price(resolved.get("price_range"))
    resolved["location"] = _clean_location(resolved.get("location"))

    if "romantic" in lowered and "romantic" not in resolved["ambiance"]:
        resolved["ambiance"].append("romantic")
        resolved["occasion"] = resolved.get("occasion") or "romantic"
    if "casual" in lowered and "casual" not in resolved["ambiance"]:
        resolved["ambiance"].append("casual")
    if "family" in lowered and "family-friendly" not in resolved["ambiance"]:
        resolved["ambiance"].append("family-friendly")

    return resolved


def _is_recommendation_query(message: str, conversation_history: Optional[List[Any]]) -> bool:
    text = (message or "").strip().lower()
    if not text:
        return False
    recommendation_terms = [
        "recommend", "suggest", "find", "best", "restaurant", "restaurants", "eat", "dine",
        "dinner", "lunch", "brunch", "breakfast", "vegan", "vegetarian", "date", "anniversary",
        "near me", "nearby", "takeout", "delivery", "open", "hours", "romantic", "casual",
    ]
    if any(term in text for term in recommendation_terms):
        return True
    return bool(_history_has_recommendations(conversation_history) and FOLLOW_UP_HINTS.search(text))


def _build_search_text(message: str, resolved: Dict[str, Any]) -> Optional[str]:
    pieces = []
    for value in resolved.get("keywords") or []:
        pieces.append(value)
    if resolved.get("occasion"):
        pieces.append(resolved["occasion"])
    if not pieces:
        lowered = (message or "").lower()
        if len(lowered.split()) <= 4 and not _clean_location(lowered):
            pieces.append(lowered)
    joined = " ".join(_dedupe([piece for piece in pieces if piece]))
    return joined or None


def _restaurant_to_recommendation(restaurant: Any) -> Dict[str, Any]:
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "avg_rating": float(restaurant.avg_rating or 0),
        "review_count": int(restaurant.review_count or 0),
        "price_range": restaurant.price_range,
        "cuisine_type": restaurant.cuisine_type,
        "address": restaurant.address,
        "city": restaurant.city,
        "state": restaurant.state,
        "image_url": getattr(restaurant, "image_url", None),
        "primary_photo": getattr(restaurant, "primary_photo", None),
        "source": getattr(restaurant, "source", None),
        "reason": None,
    }


def _restaurant_blob(restaurant: Any) -> str:
    data = [
        restaurant.name,
        restaurant.cuisine_type,
        restaurant.description,
        restaurant.address,
        restaurant.city,
        restaurant.state,
    ]
    try:
        if getattr(restaurant, "keywords", None):
            data.append(json.dumps(restaurant.keywords))
        if getattr(restaurant, "amenities", None):
            data.append(json.dumps(restaurant.amenities))
    except Exception:
        pass
    return " ".join([str(part) for part in data if part]).lower()


def _score_restaurant(restaurant: Any, resolved: Dict[str, Any], preferences: Dict[str, Any], search_text: Optional[str]) -> Tuple[float, List[str]]:
    score = float(restaurant.avg_rating or 0) * 20 + min(int(restaurant.review_count or 0), 500) / 10
    reasons: List[str] = []
    blob = _restaurant_blob(restaurant)

    cuisine = (resolved.get("cuisine") or "").lower()
    if cuisine and cuisine in (restaurant.cuisine_type or "").lower():
        score += 30
        reasons.append(f"matches your {cuisine} preference")

    for pref in preferences.get("cuisine_preferences") or []:
        pref_text = str(pref).lower()
        if pref_text and pref_text in (restaurant.cuisine_type or "").lower():
            score += 12
            if "saved preferences" not in " ".join(reasons):
                reasons.append("fits your saved cuisine preferences")
            break

    resolved_price = resolved.get("price_range")
    if resolved_price and restaurant.price_range == resolved_price:
        score += 14
        reasons.append(f"matches your {resolved_price} budget")
    elif resolved_price and restaurant.price_range:
        diff = abs(_price_rank(restaurant.price_range) - _price_rank(resolved_price))
        score += max(0, 8 - diff * 3)

    for dietary in resolved.get("dietary") or []:
        if dietary.replace("-", " ") in blob or dietary in blob:
            score += 10
            reasons.append(f"mentions {dietary.replace('-', ' ')} options")

    for ambiance in resolved.get("ambiance") or []:
        check = ambiance.replace("-", " ")
        if check in blob or ambiance in blob:
            score += 8
            reasons.append(f"has a {check} vibe")

    if resolved.get("occasion") == "romantic" and any(term in blob for term in ["romantic", "date", "upscale", "wine", "cozy"]):
        score += 10
        reasons.append("works well for a romantic outing")

    location = (resolved.get("location") or "").lower()
    if location and location in blob:
        score += 14
        reasons.append(f"is around {resolved['location']}")

    if search_text:
        for word in search_text.lower().split():
            if word in blob:
                score += 3

    return score, _dedupe(reasons)


def _maybe_enrich_with_tavily(message: str, restaurants: List[Any]) -> Dict[int, str]:
    if not restaurants:
        return {}
    try:
        from app.config import settings
        from app.services.ai_agent_tavily import search as tavily_search
    except Exception:
        return {}

    if not settings.TAVILY_URL or not CURRENT_CONTEXT_HINTS.search(message or ""):
        return {}

    context: Dict[int, str] = {}
    for restaurant in restaurants[:3]:
        query = f"{restaurant.name} {restaurant.city or ''} current hours specials events trending restaurant"
        try:
            hits = tavily_search(query, limit=1)
        except Exception:
            continue
        if hits:
            snippet = (hits[0].get("snippet") or "").strip()
            if snippet:
                context[restaurant.id] = snippet[:180]
    return context


def _build_assistant_text(
    resolved: Dict[str, Any],
    preferences: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
    used_current_context: bool,
) -> str:
    if not recommendations:
        parts = ["I couldn't find a strong match with the current filters."]
        if resolved.get("location"):
            parts.append(f"Try expanding beyond {resolved['location']}.")
        parts.append("You can also ask me for a different cuisine, budget, or vibe and I'll refine the search.")
        return " ".join(parts)

    summary_bits: List[str] = ["Here are some restaurant picks"]
    if resolved.get("location"):
        summary_bits.append(f"around {resolved['location']}")
    if resolved.get("cuisine"):
        summary_bits.append(f"for {resolved['cuisine']} food")
    if resolved.get("occasion") and resolved.get("occasion") not in ["dinner", "lunch", "brunch"]:
        summary_bits.append(f"that fit a {resolved['occasion']} occasion")
    if resolved.get("price_range"):
        summary_bits.append(f"within a {resolved['price_range']} budget")

    preference_notes: List[str] = []
    if preferences.get("cuisine_preferences"):
        preference_notes.append("your saved cuisine preferences")
    if preferences.get("dietary_restrictions"):
        preference_notes.append("your dietary settings")
    if preferences.get("ambiance_preferences"):
        preference_notes.append("your ambiance preferences")

    text = " ".join(summary_bits) + "."
    if preference_notes:
        text += f" I also used {', '.join(preference_notes)} to rank them."
    if used_current_context:
        text += " I checked current web context for the top matches when it looked relevant."
    text += " Tap any card to open the full restaurant details page."
    return text


def build_system_prompt(user: Optional[Any], prefs: Dict[str, Any]) -> str:
    parts = ["You are a restaurant recommendation assistant."]
    if user and getattr(user, "id", None):
        parts.append(f"User ID: {user.id}")
    if prefs.get("cuisine_preferences"):
        parts.append(f"Saved cuisines: {prefs['cuisine_preferences']}")
    if prefs.get("price_range"):
        parts.append(f"Saved budget: {prefs['price_range']}")
    if prefs.get("dietary_restrictions"):
        parts.append(f"Dietary restrictions: {prefs['dietary_restrictions']}")
    return "\n".join(parts)


def generate_recommendations(
    db: Session,
    user: Optional[Any],
    message: str,
    conversation_history: Optional[List[Any]] = None,
    limit: int = 5,
) -> Tuple[str, List[Dict[str, Any]]]:
    preferences = _load_user_preferences(db, user)
    history = _history_messages(conversation_history)
    extracted = _extract_with_langchain(message, history, preferences) or _simple_extract(message)
    resolved = _merge_filters(message, extracted, history, preferences)

    if not _is_recommendation_query(message, history):
        return (
            "I can help with restaurant recommendations, follow-up refinements, current hours, and vibe-based searches. "
            "Try something like 'romantic Italian dinner tonight in San Jose' or 'show me something cheaper'.",
            [],
        )

    search_text = _build_search_text(message, resolved)
    sort_by = resolved.get("sort_preference") or "recommended"

    items, _ = restaurant_service.search_restaurants(
        db,
        q=search_text,
        cuisine=resolved.get("cuisine"),
        location=resolved.get("location"),
        price_range=resolved.get("price_range"),
        sort_by=sort_by,
        page=1,
        page_size=60,
    )

    if not items and resolved.get("location"):
        items, _ = restaurant_service.search_restaurants(
            db,
            q=search_text,
            cuisine=resolved.get("cuisine"),
            location=None,
            price_range=resolved.get("price_range"),
            sort_by=sort_by,
            page=1,
            page_size=60,
        )

    if not items and search_text:
        items, _ = restaurant_service.search_restaurants(
            db,
            q=None,
            cuisine=resolved.get("cuisine"),
            location=resolved.get("location"),
            price_range=resolved.get("price_range"),
            sort_by=sort_by,
            page=1,
            page_size=60,
        )

    scored: List[Tuple[float, Any, List[str]]] = []
    for restaurant in items:
        score, reasons = _score_restaurant(restaurant, resolved, preferences, search_text)
        scored.append((score, restaurant, reasons))
    scored.sort(key=lambda row: row[0], reverse=True)

    top_rows = scored[:limit]
    web_context = _maybe_enrich_with_tavily(message, [row[1] for row in top_rows])

    recommendations: List[Dict[str, Any]] = []
    for _, restaurant, reasons in top_rows:
        rec = _restaurant_to_recommendation(restaurant)
        final_reasons = list(reasons)
        if restaurant.id in web_context:
            final_reasons.append(f"current web note: {web_context[restaurant.id]}")
        rec["reason"] = "; ".join(_dedupe(final_reasons)) or "strong overall match for your request"
        recommendations.append(rec)

    assistant_text = _build_assistant_text(resolved, preferences, recommendations, bool(web_context))
    return assistant_text, recommendations


def _chunk_text(text: str, chunk_size: int = 220) -> List[str]:
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    buffer = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(buffer) + len(sentence) + 1 <= chunk_size:
            buffer = f"{buffer} {sentence}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            buffer = sentence
    if buffer:
        chunks.append(buffer)
    return chunks or [text]


def stream_recommendations(
    db: Session,
    user: Optional[Any],
    message: str,
    conversation_history: Optional[List[Any]] = None,
    limit: int = 5,
):
    assistant_text, recommendations = generate_recommendations(
        db,
        user,
        message,
        conversation_history,
        limit=limit,
    )
    for chunk in _chunk_text(assistant_text):
        yield ("assistant_chunk", chunk)
    for recommendation in recommendations:
        yield ("recommendation", recommendation)
    return assistant_text, recommendations
