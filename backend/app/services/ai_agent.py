from __future__ import annotations

import json
import logging
import math
import re
from typing import Any, Dict, Generator, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.services import restaurant_service
from app.services.user_service import get_user_by_id

logger = logging.getLogger(__name__)

COMMON_CUISINES = [
    "italian",
    "chinese",
    "mexican",
    "indian",
    "japanese",
    "thai",
    "french",
    "american",
    "mediterranean",
    "korean",
    "vietnamese",
    "greek",
    "pizza",
    "sushi",
    "seafood",
    "bbq",
    "burgers",
    "dessert",
    "coffee",
    "brunch",
]

DIETARY_TERMS = [
    "vegetarian",
    "vegan",
    "halal",
    "gluten-free",
    "gluten free",
    "kosher",
    "dairy-free",
    "dairy free",
    "pescatarian",
]

AMBIANCE_TERMS = [
    "casual",
    "fine dining",
    "family-friendly",
    "family friendly",
    "romantic",
    "outdoor seating",
    "wifi",
    "quiet",
    "lively",
    "cozy",
    "upscale",
    "trendy",
    "brunch",
    "date night",
    "bar",
    "rooftop",
]

BAD_LOCATION_VALUES = {
    "me",
    "here",
    "there",
    "near me",
    "around me",
    "my area",
    "nearby",
    "close to me",
    "close by",
    "local",
}

FOLLOW_UP_HINTS = re.compile(
    r"\b(another|else|instead|same|similar|cheaper|pricier|expensive|more expensive|less expensive|romantic|casual|closer|nearer|more|less|what about|how about)\b",
    re.IGNORECASE,
)

FALLBACK_RESTAURANT_HINTS = re.compile(
    r"\b(recommend|suggest|find|best|restaurant|restaurants|eat|dine|dinner|lunch|brunch|breakfast|pizza|vegan|vegetarian|date|anniversary|takeout|delivery|romantic|casual|near me|nearby)\b",
    re.IGNORECASE,
)

FALLBACK_TAVILY_HINTS = re.compile(
    r"\b(open|opening|hours|hour|tonight|today|tomorrow|weekend|current|trending|special|event|events|busy|popular|calories|calorie|nutrition|protein|fat|carbs|carbohydrates|healthy|ingredients|menu|reservation|reservations)\b",
    re.IGNORECASE,
)

SORT_MAP = {
    "rating": "rating",
    "best": "rating",
    "best rated": "rating",
    "top rated": "rating",
    "popular": "review_count",
    "popularity": "review_count",
    "reviews": "review_count",
    "review_count": "review_count",
    "price": "price",
    "cheapest": "price",
    "lowest price": "price",
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
    follow_up_mode: bool = False


class RouterDecision(BaseModel):
    intent: str = "restaurant_search"
    use_restaurant_db: bool = True
    use_tavily: bool = False
    tavily_query: Optional[str] = None


class ClientLocation(BaseModel):
    latitude: float
    longitude: float


def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _empty_filters() -> Dict[str, Any]:
    return {
        "cuisine": None,
        "price_range": None,
        "dietary": [],
        "occasion": None,
        "ambiance": [],
        "location": None,
        "keywords": [],
        "sort_preference": None,
        "wants_current_context": False,
        "follow_up_mode": False,
    }


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _normalize_price(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    text = str(value).strip()
    dollars = text.count("$")
    if dollars:
        return "$" * min(max(dollars, 1), 4)

    lowered = text.lower()
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
    return SORT_MAP.get(str(value).strip().lower(), "recommended")


def _clean_location(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    cleaned = re.sub(
        r"\b(please|thanks|thank you|tonight|today|now)\b",
        "",
        str(value),
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
    if not cleaned:
        return None

    lowered = cleaned.lower()
    if lowered in BAD_LOCATION_VALUES:
        return None
    if lowered.startswith("near ") and lowered[5:] in {"me", "here"}:
        return None
    if lowered.startswith("around ") and lowered[7:] in {"me", "here"}:
        return None
    return cleaned


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


def _history_filters(conversation_history: Optional[List[Any]]) -> List[Dict[str, Any]]:
    filters: List[Dict[str, Any]] = []
    for item in _history_messages(conversation_history):
        parsed = item.get("parsed_filters")
        if isinstance(parsed, dict):
            filters.append(parsed)
    return filters


def _last_history_filters(conversation_history: Optional[List[Any]]) -> Dict[str, Any]:
    filters = _history_filters(conversation_history)
    if not filters:
        return _empty_filters()
    return dict(_empty_filters(), **filters[-1])


def _build_history_summary(conversation_history: Optional[List[Any]], limit: int = 6) -> str:
    lines: List[str] = []
    for item in _history_messages(conversation_history)[-limit:]:
        role = str(item.get("role") or "user")
        content = str(item.get("content") or "").strip()
        parsed = item.get("parsed_filters")
        if content:
            line = f"{role}: {content[:220]}"
            if isinstance(parsed, dict):
                line += f" | parsed_filters={json.dumps(parsed, ensure_ascii=False)}"
            lines.append(line)
    return "\n".join(lines)


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def _call_ollama_json(prompt: str, max_tokens: int = 400) -> Optional[Dict[str, Any]]:
    try:
        from app.config import settings
        from app.services.ai_agent_ollama import call_ollama
    except Exception as exc:
        logger.debug("Ollama imports unavailable: %s", exc)
        return None

    if not getattr(settings, "OLLAMA_URL", None) or not getattr(settings, "OLLAMA_MODEL", None):
        return None

    try:
        raw = call_ollama(prompt, max_tokens=max_tokens, temperature=0.0)
        return _extract_json_object(str(raw or ""))
    except Exception as exc:
        logger.debug("Ollama call failed: %s", exc)
        return None


def _normalize_extracted_dict(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    data = dict(_empty_filters())
    if not isinstance(payload, dict):
        return data

    merged = dict(data)
    merged.update(payload)
    try:
        model = ExtractedQuery(**merged)
        data = _model_to_dict(model)
    except ValidationError as exc:
        logger.debug("Invalid extracted payload: %s", exc)
        return data

    cuisine = data.get("cuisine")
    if cuisine:
        cuisine_text = str(cuisine).strip().lower()
        data["cuisine"] = "japanese" if cuisine_text == "sushi" else cuisine_text

    data["price_range"] = _normalize_price(data.get("price_range"))
    data["location"] = _clean_location(data.get("location"))
    data["sort_preference"] = _normalize_sort(data.get("sort_preference"))
    data["dietary"] = _dedupe([str(item).strip().lower().replace(" ", "-") for item in (data.get("dietary") or [])])
    data["ambiance"] = _dedupe([str(item).strip().lower().replace(" ", "-") for item in (data.get("ambiance") or [])])
    data["keywords"] = _dedupe([str(item).strip().lower() for item in (data.get("keywords") or [])])
    data["wants_current_context"] = bool(data.get("wants_current_context"))
    data["follow_up_mode"] = bool(data.get("follow_up_mode"))
    return data


def _simple_extract(message: str) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = text.lower()
    extracted = _empty_filters()
    extracted["wants_current_context"] = bool(FALLBACK_TAVILY_HINTS.search(text))
    extracted["follow_up_mode"] = bool(FOLLOW_UP_HINTS.search(text))

    for cuisine in COMMON_CUISINES:
        if re.search(rf"\b{re.escape(cuisine)}\b", lowered):
            extracted["cuisine"] = "japanese" if cuisine == "sushi" else cuisine
            break

    if any(word in lowered for word in ["cheap", "budget", "affordable"]):
        extracted["price_range"] = "$"
    elif any(word in lowered for word in ["mid-range", "mid range", "moderate"]):
        extracted["price_range"] = "$$"
    elif any(word in lowered for word in ["expensive", "fancy", "upscale"]):
        extracted["price_range"] = "$$$"

    for term in DIETARY_TERMS:
        if term in lowered:
            extracted["dietary"].append(term.replace(" ", "-"))

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

    if "near me" not in lowered and "around me" not in lowered and "nearby" not in lowered:
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
        keyword_hits.append(str(extracted["occasion"]))

    extracted["keywords"] = _dedupe(keyword_hits)
    extracted["dietary"] = _dedupe(extracted["dietary"])
    extracted["ambiance"] = _dedupe(extracted["ambiance"])
    return _normalize_extracted_dict(extracted)


def _extract_with_ollama(message: str, conversation_history: Optional[List[Any]], preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    previous_filters = _last_history_filters(conversation_history)
    history_summary = _build_history_summary(conversation_history)

    prompt = f"""
You extract restaurant assistant filters from chat messages.

Return ONLY a valid JSON object.
Do not add markdown.
Do not add explanations.

Schema:
{{
  "cuisine": string | null,
  "price_range": "$" | "$$" | "$$$" | "$$$$" | null,
  "dietary": string[],
  "occasion": string | null,
  "ambiance": string[],
  "location": string | null,
  "keywords": string[],
  "sort_preference": "rating" | "review_count" | "price" | "recommended" | "newest" | null,
  "wants_current_context": boolean,
  "follow_up_mode": boolean
}}

Rules:
- If the user says "near me", "around me", "nearby", "here", or "close to me", set "location" to null. Never output "me" as a location.
- Use follow_up_mode=true when the user is refining a previous request like "something cheaper", "same but vegan", "pizza instead", or "another one".
- For nutrition or food-fact questions, keep restaurant filters empty unless the message also clearly asks for restaurant recommendations.
- Keep dietary and ambiance items short and lowercase.
- Keep cuisine lowercase.
- Keep keywords short and useful.

Saved user preferences:
{json.dumps(preferences, ensure_ascii=False)}

Most recent structured filters:
{json.dumps(previous_filters, ensure_ascii=False)}

Recent conversation:
{history_summary or "(none)"}

Latest user message:
{message}
""".strip()

    parsed = _call_ollama_json(prompt, max_tokens=350)
    if not parsed:
        return None
    return _normalize_extracted_dict(parsed)


def _route_with_ollama(message: str, conversation_history: Optional[List[Any]], preferences: Dict[str, Any], extracted: Dict[str, Any]) -> Optional[RouterDecision]:
    history_summary = _build_history_summary(conversation_history)
    prompt = f"""
You are the routing model for a restaurant web app assistant.

Your job is to decide whether the assistant should use:
1. the restaurant database
2. Tavily web search
3. both
4. neither

Return ONLY a valid JSON object.
Do not add markdown.
Do not add explanations.

Schema:
{{
  "intent": "restaurant_search" | "restaurant_current_info" | "food_info" | "general_chat",
  "use_restaurant_db": boolean,
  "use_tavily": boolean,
  "tavily_query": string | null
}}

Important routing policy:
- The restaurant database is the primary source for restaurant recommendations.
- Tavily is the primary source for live or web-dependent information.
- Use BOTH database and Tavily whenever the user wants restaurant recommendations that may benefit from fresh web context.
- Fresh web context includes: open now, hours, closing time, tonight, today, tomorrow, weekend, specials, events, trending, busy, currently popular, or live restaurant info.
- Use Tavily for nutrition, calories, ingredients, protein, carbs, healthiness, and other food-fact questions.
- Use Tavily for named-restaurant factual questions like menu, hours, reservations, specials, or current info.
- Use restaurant_search when the user wants recommendations like best, top-rated, cheap, romantic, vegan, pizza, sushi, near me, nearby, or similar discovery requests.
- For follow-up recommendation requests like "something cheaper", "another one", "same but vegan", or "pizza instead", keep use_restaurant_db=true.
- If the message asks for recommendations near the user and also implies freshness or real-world context, set use_tavily=true.
- If the message is a pure recommendation request with no need for live info, set use_tavily=false.
- Never set location text to "me". "near me" means nearby search handled by the app, not a literal location string.

Decision examples:
- "Best rated near me" -> restaurant_search, use_restaurant_db=true, use_tavily=false
- "Best rated near me open now" -> restaurant_current_info, use_restaurant_db=true, use_tavily=true
- "What time does Nopa close tonight?" -> restaurant_current_info, use_restaurant_db=false, use_tavily=true
- "How many calories does turkey have?" -> food_info, use_restaurant_db=false, use_tavily=true
- "Something cheaper" after restaurant results -> restaurant_search, use_restaurant_db=true, use_tavily=false
- "Popular sushi places near me tonight" -> restaurant_current_info, use_restaurant_db=true, use_tavily=true

Saved preferences:
{json.dumps(preferences, ensure_ascii=False)}

Parsed filters for latest message:
{json.dumps(extracted, ensure_ascii=False)}

Recent conversation:
{history_summary or "(none)"}

Latest user message:
{message}
""".strip()

    parsed = _call_ollama_json(prompt, max_tokens=260)
    if not parsed:
        return None
    try:
        return RouterDecision(**parsed)
    except ValidationError as exc:
        logger.debug("Invalid router payload: %s", exc)
        return None


def _fallback_route(message: str, extracted: Dict[str, Any], conversation_history: Optional[List[Any]]) -> RouterDecision:
    text = (message or "").strip().lower()
    if _history_has_recommendations(conversation_history) and FOLLOW_UP_HINTS.search(text):
        return RouterDecision(intent="restaurant_search", use_restaurant_db=True, use_tavily=False, tavily_query=None)
    if FALLBACK_RESTAURANT_HINTS.search(text) and FALLBACK_TAVILY_HINTS.search(text):
        return RouterDecision(intent="restaurant_current_info", use_restaurant_db=True, use_tavily=True, tavily_query=message.strip())
    if FALLBACK_TAVILY_HINTS.search(text) and not FALLBACK_RESTAURANT_HINTS.search(text):
        return RouterDecision(intent="food_info", use_restaurant_db=False, use_tavily=True, tavily_query=message.strip())
    if FALLBACK_RESTAURANT_HINTS.search(text) or extracted.get("follow_up_mode"):
        return RouterDecision(intent="restaurant_search", use_restaurant_db=True, use_tavily=False, tavily_query=None)
    return RouterDecision(intent="general_chat", use_restaurant_db=False, use_tavily=False, tavily_query=None)


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


def _merge_filters(message: str, extracted: Dict[str, Any], conversation_history: Optional[List[Any]], preferences: Dict[str, Any]) -> Dict[str, Any]:
    resolved = dict(_empty_filters())
    resolved.update(extracted or {})
    previous = _last_history_filters(conversation_history)
    lowered = (message or "").lower()

    is_follow_up = bool(
        resolved.get("follow_up_mode")
        or (FOLLOW_UP_HINTS.search(lowered) and (previous != _empty_filters() or _history_has_recommendations(conversation_history)))
    )

    if is_follow_up:
        for key in ["cuisine", "price_range", "occasion", "location", "sort_preference"]:
            if not resolved.get(key) and previous.get(key):
                resolved[key] = previous.get(key)
        resolved["dietary"] = _dedupe((previous.get("dietary") or []) + (resolved.get("dietary") or []))
        resolved["ambiance"] = _dedupe((previous.get("ambiance") or []) + (resolved.get("ambiance") or []))
        resolved["keywords"] = _dedupe((previous.get("keywords") or []) + (resolved.get("keywords") or []))
        resolved["wants_current_context"] = bool(resolved.get("wants_current_context") or previous.get("wants_current_context"))

    base_price = resolved.get("price_range") or previous.get("price_range") or preferences.get("price_range")
    if "cheaper" in lowered or "less expensive" in lowered:
        rank = max(_price_rank(base_price) - 1, 1)
        resolved["price_range"] = "$" * rank
        resolved["sort_preference"] = "price"
    elif any(word in lowered for word in ["pricier", "more expensive", "fancier", "nicer", "upscale"]):
        rank = min(max(_price_rank(base_price), 1) + 1, 4)
        resolved["price_range"] = "$" * rank

    if "same" in lowered and is_follow_up:
        for key in ["cuisine", "price_range", "occasion", "location", "sort_preference"]:
            if previous.get(key):
                resolved[key] = previous.get(key)
        resolved["dietary"] = _dedupe((previous.get("dietary") or []) + (resolved.get("dietary") or []))
        resolved["ambiance"] = _dedupe((previous.get("ambiance") or []) + (resolved.get("ambiance") or []))
        resolved["keywords"] = _dedupe((previous.get("keywords") or []) + (resolved.get("keywords") or []))

    if not resolved.get("cuisine") and preferences.get("cuisine_preferences"):
        resolved["cuisine"] = preferences["cuisine_preferences"][0]
    if not resolved.get("price_range") and preferences.get("price_range"):
        resolved["price_range"] = preferences["price_range"]
    if not resolved.get("location") and preferences.get("preferred_locations") and not re.search(r"\b(near me|around me|nearby|here)\b", lowered, re.IGNORECASE):
        resolved["location"] = preferences["preferred_locations"][0]
    if not resolved.get("sort_preference") and preferences.get("sort_preference"):
        resolved["sort_preference"] = preferences["sort_preference"]

    resolved["dietary"] = _dedupe((resolved.get("dietary") or []) + (preferences.get("dietary_restrictions") or []))
    resolved["ambiance"] = _dedupe((resolved.get("ambiance") or []) + (preferences.get("ambiance_preferences") or []))

    if "romantic" in lowered and "romantic" not in resolved["ambiance"]:
        resolved["ambiance"].append("romantic")
        resolved["occasion"] = resolved.get("occasion") or "romantic"
    if "casual" in lowered and "casual" not in resolved["ambiance"]:
        resolved["ambiance"].append("casual")
    if "family" in lowered and "family-friendly" not in resolved["ambiance"]:
        resolved["ambiance"].append("family-friendly")

    resolved["price_range"] = _normalize_price(resolved.get("price_range"))
    resolved["location"] = _clean_location(resolved.get("location"))
    resolved["sort_preference"] = _normalize_sort(resolved.get("sort_preference"))
    resolved["dietary"] = _dedupe([str(x).lower() for x in (resolved.get("dietary") or [])])
    resolved["ambiance"] = _dedupe([str(x).lower() for x in (resolved.get("ambiance") or [])])
    resolved["keywords"] = _dedupe([str(x).lower() for x in (resolved.get("keywords") or [])])
    resolved["wants_current_context"] = bool(resolved.get("wants_current_context"))
    resolved["follow_up_mode"] = bool(is_follow_up)
    return resolved


def _build_search_text(message: str, resolved: Dict[str, Any]) -> Optional[str]:
    pieces: List[str] = []
    for value in resolved.get("keywords") or []:
        pieces.append(value)
    if resolved.get("occasion"):
        pieces.append(str(resolved["occasion"]))
    joined = " ".join(_dedupe([piece for piece in pieces if piece]))
    if joined:
        return joined
    lowered = (message or "").strip().lower()
    if len(lowered.split()) <= 4 and not resolved.get("location"):
        return lowered
    return None


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
        "latitude": getattr(restaurant, "latitude", None),
        "longitude": getattr(restaurant, "longitude", None),
        "reason": None,
    }


def _restaurant_blob(restaurant: Any) -> str:
    parts = [
        getattr(restaurant, "name", None),
        getattr(restaurant, "cuisine_type", None),
        getattr(restaurant, "description", None),
        getattr(restaurant, "address", None),
        getattr(restaurant, "city", None),
        getattr(restaurant, "state", None),
    ]
    try:
        if getattr(restaurant, "keywords", None):
            parts.append(json.dumps(restaurant.keywords))
        if getattr(restaurant, "amenities", None):
            parts.append(json.dumps(restaurant.amenities))
    except Exception:
        pass
    return " ".join([str(part) for part in parts if part]).lower()


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_miles * c


def _score_restaurant(restaurant: Any, resolved: Dict[str, Any], preferences: Dict[str, Any], search_text: Optional[str], client_location: Optional[Dict[str, float]] = None) -> Tuple[float, List[str]]:
    score = float(restaurant.avg_rating or 0) * 20 + min(int(restaurant.review_count or 0), 500) / 10
    reasons: List[str] = []
    blob = _restaurant_blob(restaurant)

    cuisine = (resolved.get("cuisine") or "").lower()
    if cuisine and cuisine in (getattr(restaurant, "cuisine_type", "") or "").lower():
        score += 30
        reasons.append(f"matches your {cuisine} preference")

    for pref in preferences.get("cuisine_preferences") or []:
        pref_text = str(pref).lower()
        if pref_text and pref_text in (getattr(restaurant, "cuisine_type", "") or "").lower():
            score += 12
            if "fits your saved cuisine preferences" not in reasons:
                reasons.append("fits your saved cuisine preferences")
            break

    resolved_price = resolved.get("price_range")
    restaurant_price = getattr(restaurant, "price_range", None)
    if resolved_price and restaurant_price == resolved_price:
        score += 14
        reasons.append(f"matches your {resolved_price} budget")
    elif resolved_price and restaurant_price:
        diff = abs(_price_rank(restaurant_price) - _price_rank(resolved_price))
        score += max(0, 8 - diff * 3)

    for dietary in resolved.get("dietary") or []:
        token = dietary.replace("-", " ")
        if token in blob or dietary in blob:
            score += 10
            reasons.append(f"mentions {token} options")

    for ambiance in resolved.get("ambiance") or []:
        token = ambiance.replace("-", " ")
        if token in blob or ambiance in blob:
            score += 8
            reasons.append(f"has a {token} vibe")

    if resolved.get("occasion") == "romantic" and any(term in blob for term in ["romantic", "date", "upscale", "wine", "cozy"]):
        score += 10
        reasons.append("works well for a romantic outing")

    location = (resolved.get("location") or "").lower()
    if location and location in blob:
        score += 14
        reasons.append(f"is around {resolved['location']}")

    if client_location and getattr(restaurant, "latitude", None) is not None and getattr(restaurant, "longitude", None) is not None:
        try:
            miles = _haversine_miles(
                float(client_location["latitude"]),
                float(client_location["longitude"]),
                float(restaurant.latitude),
                float(restaurant.longitude),
            )
            if miles <= 2:
                score += 25
                reasons.append("very close to your location")
            elif miles <= 5:
                score += 18
                reasons.append("near your location")
            elif miles <= 10:
                score += 10
                reasons.append("within a short drive")
        except Exception:
            pass

    if search_text:
        for word in search_text.lower().split():
            if word in blob:
                score += 3
    return score, _dedupe(reasons)


def _query_tavily(query: str, limit: int = 5) -> Dict[str, Any]:
    try:
        from app.config import settings
        from app.services.ai_agent_tavily import search as tavily_search
    except Exception as exc:
        logger.debug("Tavily imports unavailable: %s", exc)
        return {}

    if not getattr(settings, "TAVILY_URL", None):
        return {}

    try:
        return tavily_search(query, limit=limit) or {}
    except Exception as exc:
        logger.debug("Tavily search failed: %s", exc)
        return {}


def _summarize_tavily_response(response: Dict[str, Any], max_results: int = 3) -> Optional[str]:
    if not response or not isinstance(response, dict):
        return None

    answer = str(response.get("answer") or "").strip()
    if answer:
        return answer

    snippets: List[str] = []

    for hit in (response.get("results") or [])[:max_results]:
        if not isinstance(hit, dict):
            continue

        content = str(hit.get("content") or "").strip()
        raw_content = str(hit.get("raw_content") or "").strip()

        if content:
            snippets.append(content)
        elif raw_content:
            snippets.append(raw_content[:700])

    if not snippets:
        return None

    return " ".join(snippets[:2]).strip()


def _maybe_enrich_with_tavily(route: RouterDecision, restaurants: List[Any]) -> Dict[int, str]:
    if not restaurants or not route.use_tavily:
        return {}
    context: Dict[int, str] = {}
    for restaurant in restaurants[:3]:
        query = f"{restaurant.name} {getattr(restaurant, 'city', '') or ''} current hours specials events trending restaurant".strip()
        hits = _query_tavily(query, limit=1)
        response = _query_tavily(query, limit=1)
        summary = _summarize_tavily_response(response)
        if summary:
            context[restaurant.id] = summary[:180]
    return context


def _build_assistant_text(resolved: Dict[str, Any], preferences: Dict[str, Any], recommendations: List[Dict[str, Any]], used_current_context: bool) -> str:
    if not recommendations:
        parts = ["I couldn't find a strong match with the current filters."]
        if resolved.get("location"):
            parts.append(f"Try expanding beyond {resolved['location']}.")
        else:
            parts.append("Try broadening the cuisine, budget, or vibe.")
        parts.append("You can also ask me for a different cuisine, budget, or vibe and I'll refine the search.")
        return " ".join(parts)

    summary_bits: List[str] = ["Here are some restaurant picks"]
    if resolved.get("location"):
        summary_bits.append(f"around {resolved['location']}")
    elif recommendations and any("location" in (rec.get("reason") or "") for rec in recommendations):
        summary_bits.append("near you")
    if resolved.get("cuisine"):
        summary_bits.append(f"for {resolved['cuisine']} food")
    if resolved.get("occasion") and resolved.get("occasion") not in ["dinner", "lunch", "brunch"]:
        summary_bits.append(f"that fit a {resolved['occasion']} occasion")
    if resolved.get("price_range"):
        summary_bits.append(f"within a {resolved['price_range']} budget")

    text = " ".join(summary_bits) + "."
    preference_notes: List[str] = []
    if preferences.get("cuisine_preferences"):
        preference_notes.append("your saved cuisine preferences")
    if preferences.get("dietary_restrictions"):
        preference_notes.append("your dietary settings")
    if preferences.get("ambiance_preferences"):
        preference_notes.append("your ambiance preferences")
    if preference_notes:
        text += f" I also used {', '.join(preference_notes)} to rank them."
    if used_current_context:
        text += " I checked current web context for the top matches where it looked relevant."
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


def parse_user_filters(db: Session, user: Optional[Any], message: str, conversation_history: Optional[List[Any]] = None) -> Dict[str, Any]:
    preferences = _load_user_preferences(db, user)
    history = _history_messages(conversation_history)
    extracted = _extract_with_ollama(message, history, preferences) or _simple_extract(message)
    return _merge_filters(message, extracted, history, preferences)


def generate_recommendations_payload(
    db: Session,
    user: Optional[Any],
    message: str,
    conversation_history: Optional[List[Any]] = None,
    client_location: Optional[Dict[str, float]] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    preferences = _load_user_preferences(db, user)
    history = _history_messages(conversation_history)

    extracted = _extract_with_ollama(message, history, preferences) or _simple_extract(message)
    resolved = _merge_filters(message, extracted, history, preferences)
    route = _route_with_ollama(message, history, preferences, resolved) or _fallback_route(message, resolved, history)

    if route.use_tavily and not route.use_restaurant_db:
        tavily_query = route.tavily_query or message.strip()
        direct_response = _query_tavily(tavily_query, limit=3)
        print(direct_response)
        direct_answer = _summarize_tavily_response(direct_response)
        print(direct_answer)
        if direct_answer:
            return {
                "assistant_text": direct_answer,
                "recommendations": [],
                "parsed_filters": resolved,
                "route": _model_to_dict(route),
                "used_current_context": True,
            }
        return {
            "assistant_text": "I couldn't find reliable current web information for that request.",
            "recommendations": [],
            "parsed_filters": resolved,
            "route": _model_to_dict(route),
            "used_current_context": True,
        }

    if not route.use_restaurant_db:
        return {
            "assistant_text": "I can help with restaurant recommendations, follow-up refinements, restaurant hours, and food-related questions.",
            "recommendations": [],
            "parsed_filters": resolved,
            "route": _model_to_dict(route),
            "used_current_context": False,
        }

    search_text = _build_search_text(message, resolved)
    sort_by = resolved.get("sort_preference") or "recommended"
    lat = client_location.get("latitude") if client_location else None
    lon = client_location.get("longitude") if client_location else None

    items, _ = restaurant_service.search_restaurants(
        db,
        q=search_text,
        cuisine=resolved.get("cuisine"),
        location=resolved.get("location"),
        price_range=resolved.get("price_range"),
        latitude=lat,
        longitude=lon,
        radius_miles=preferences.get("search_radius_miles", 10),
        sort_by=sort_by,
        page=1,
        page_size=80,
    )

    if not items and resolved.get("location"):
        items, _ = restaurant_service.search_restaurants(
            db,
            q=search_text,
            cuisine=resolved.get("cuisine"),
            location=None,
            price_range=resolved.get("price_range"),
            latitude=lat,
            longitude=lon,
            radius_miles=preferences.get("search_radius_miles", 10),
            sort_by=sort_by,
            page=1,
            page_size=80,
        )

    if not items and search_text:
        items, _ = restaurant_service.search_restaurants(
            db,
            q=None,
            cuisine=resolved.get("cuisine"),
            location=resolved.get("location"),
            price_range=resolved.get("price_range"),
            latitude=lat,
            longitude=lon,
            radius_miles=preferences.get("search_radius_miles", 10),
            sort_by=sort_by,
            page=1,
            page_size=80,
        )

    scored: List[Tuple[float, Any, List[str]]] = []
    for restaurant in items:
        score, reasons = _score_restaurant(restaurant, resolved, preferences, search_text, client_location=client_location)
        scored.append((score, restaurant, reasons))
    scored.sort(key=lambda row: row[0], reverse=True)

    top_rows = scored[:limit]
    web_context = _maybe_enrich_with_tavily(route, [row[1] for row in top_rows])

    recommendations: List[Dict[str, Any]] = []
    for _, restaurant, reasons in top_rows:
        rec = _restaurant_to_recommendation(restaurant)
        final_reasons = list(reasons)
        if restaurant.id in web_context:
            final_reasons.append(f"current web note: {web_context[restaurant.id]}")
        rec["reason"] = "; ".join(_dedupe(final_reasons)) or "strong overall match for your request"
        recommendations.append(rec)

    assistant_text = _build_assistant_text(resolved, preferences, recommendations, bool(web_context))
    logger.info(
    "AI route intent=%s use_restaurant_db=%s use_tavily=%s tavily_query=%s",
    route.intent,
    route.use_restaurant_db,
    route.use_tavily,
    route.tavily_query,
    )
    return {
        "assistant_text": assistant_text,
        "recommendations": recommendations,
        "parsed_filters": resolved,
        "route": _model_to_dict(route),
        "used_current_context": bool(web_context),
    }


def generate_recommendations(db: Session, user: Optional[Any], message: str, conversation_history: Optional[List[Any]] = None, client_location: Optional[Dict[str, float]] = None, limit: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
    payload = generate_recommendations_payload(
        db=db,
        user=user,
        message=message,
        conversation_history=conversation_history,
        client_location=client_location,
        limit=limit,
    )
    return payload["assistant_text"], payload["recommendations"]


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
    client_location: Optional[Dict[str, float]] = None,
    limit: int = 5,
) -> Generator[Tuple[str, Any], None, Tuple[str, List[Dict[str, Any]]]]:
    payload = generate_recommendations_payload(
        db=db,
        user=user,
        message=message,
        conversation_history=conversation_history,
        client_location=client_location,
        limit=limit,
    )
    assistant_text = payload["assistant_text"]
    recommendations = payload["recommendations"]
    for chunk in _chunk_text(assistant_text):
        yield ("assistant_chunk", chunk)
    for recommendation in recommendations:
        yield ("recommendation", recommendation)
    return assistant_text, recommendations
