from typing import Any, Dict, List, Optional
import logging
import requests

from app.config import settings

logger = logging.getLogger(__name__)


def search(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Call Tavily Search and return the full JSON response.

    Expected useful fields:
    - response["answer"] when include_answer is enabled
    - response["results"][i]["content"]
    - response["results"][i]["raw_content"] when include_raw_content is enabled
    """
    if not settings.TAVILY_URL:
        raise RuntimeError("Tavily not configured: set TAVILY_URL")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if settings.TAVILY_API_KEY:
        headers["Authorization"] = f"Bearer {settings.TAVILY_API_KEY}"

    payload = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": "advanced",
        "include_raw_content": True,
        "max_results": limit,
        "topic": "general",
    }

    try:
        resp = requests.post(
            settings.TAVILY_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to reach Tavily endpoint: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"Tavily returned status {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Tavily returned non-JSON response: {e}") from e

    try:
        logger.info(
            "Tavily.search answer_present=%s results=%s",
            bool(data.get("answer")),
            len(data.get("results") or []),
        )
    except Exception:
        pass

    return data


def extract(url: str, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Call Tavily Extract for a specific URL and return the full JSON response.
    """
    if not settings.TAVILY_URL:
        raise RuntimeError("Tavily not configured: set TAVILY_URL")

    if settings.TAVILY_URL.endswith("/search"):
        extract_endpoint = settings.TAVILY_URL.replace("/search", "/extract")
    else:
        extract_endpoint = "https://api.tavily.com/extract"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if settings.TAVILY_API_KEY:
        headers["Authorization"] = f"Bearer {settings.TAVILY_API_KEY}"

    payload: Dict[str, Any] = {"urls": [url]}
    if query:
        payload["query"] = query
        payload["chunks_per_source"] = 3

    try:
        resp = requests.post(
            extract_endpoint,
            json=payload,
            headers=headers,
            timeout=20,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to call Tavily extract endpoint: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"Tavily extract returned {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except Exception:
        return {"raw_text": resp.text}

    return data