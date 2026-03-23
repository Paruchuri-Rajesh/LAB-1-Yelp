from typing import Any, Dict, List
import logging
import requests
from app.config import settings

logger = logging.getLogger(__name__)


def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Call a Tavily endpoint (generic wrapper) and return a list of search hits.

    Each hit will be a dict with keys: 'title', 'snippet', 'url'. The implementation
    is intentionally permissive since Tavily deployments differ. If the Tavily
    endpoint or API key is not configured this raises RuntimeError.
    """
    if not settings.TAVILY_URL:
        raise RuntimeError("Tavily not configured: set TAVILY_URL")

    headers = {"Accept": "application/json"}
    if settings.TAVILY_API_KEY:
        headers["Authorization"] = f"Bearer {settings.TAVILY_API_KEY}"

    # First try a GET with q param
    try:
        resp = requests.get(settings.TAVILY_URL, params={"q": query, "limit": limit}, headers=headers, timeout=8)
    except Exception:
        resp = None

    # If GET failed or returned non-JSON, try POST
    if resp is None or resp.status_code != 200:
        try:
            resp = requests.post(settings.TAVILY_URL, json={"query": query, "limit": limit}, headers=headers, timeout=8)
        except Exception as e:
            raise RuntimeError(f"Failed to reach Tavily endpoint: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"Tavily returned status {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Tavily returned non-JSON response: {e}") from e

    hits: List[Dict[str, Any]] = []
    # If the service returns a list of results directly
    if isinstance(data, list):
        for item in data[:limit]:
            if isinstance(item, dict):
                title = item.get("title") or item.get("headline") or item.get("name")
                snippet = item.get("snippet") or item.get("summary") or item.get("excerpt") or ""
                url = item.get("url") or item.get("link") or item.get("source") or ""
                hits.append({"title": title, "snippet": snippet, "url": url})
        return hits

    # If data is dict, try to find a hits/results key
    if isinstance(data, dict):
        for key in ("results", "hits", "items", "articles"):
            arr = data.get(key)
            if isinstance(arr, list):
                for item in arr[:limit]:
                    if isinstance(item, dict):
                        title = item.get("title") or item.get("headline") or item.get("name")
                        snippet = item.get("snippet") or item.get("summary") or item.get("excerpt") or ""
                        url = item.get("url") or item.get("link") or item.get("source") or ""
                        hits.append({"title": title, "snippet": snippet, "url": url})
                if hits:
                    try:
                        logger.info("Tavily.search parsed hits (truncated): %s", str(hits)[:1000])
                    except Exception:
                        pass
                    return hits

    # If we couldn't find structured hits, try to coerce any strings
    text = str(data)
    hits.append({"title": "Search results", "snippet": text[:500], "url": ""})
    try:
        logger.info("Tavily.search fallback data (truncated): %s", text[:1000])
    except Exception:
        pass
    return hits


def extract(url: str) -> Dict[str, Any]:
    """Call the Tavily Extract API to retrieve structured content for a specific URL.

    Returns a dict with keys like 'title', 'content', 'text', or raw JSON when available.
    """
    if not settings.TAVILY_URL:
        raise RuntimeError("Tavily not configured: set TAVILY_URL")

    # Prefer a dedicated extract endpoint if known
    extract_endpoint = None
    if settings.TAVILY_URL.endswith("/search"):
        extract_endpoint = settings.TAVILY_URL.replace("/search", "/extract")
    else:
        extract_endpoint = "https://api.tavily.com/extract"

    headers = {"Accept": "application/json"}
    if settings.TAVILY_API_KEY:
        headers["Authorization"] = f"Bearer {settings.TAVILY_API_KEY}"

    try:
        # Tavily Extract expects a list of urls under the 'urls' field in many deployments.
        # Send as {"urls": [url]} to be permissive.
        resp = requests.post(extract_endpoint, json={"urls": [url]}, headers=headers, timeout=10)
    except Exception as e:
        raise RuntimeError(f"Failed to call Tavily extract endpoint: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"Tavily extract returned {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except Exception:
        # fallback to raw text
        try:
            logger.info("Tavily.extract returned non-json text for %s: %s", url, resp.text[:1000])
        except Exception:
            pass
        return {"text": resp.text}

    # normalize common fields
    out = {}
    if isinstance(data, dict):
        out["title"] = data.get("title") or data.get("headline")
        # prefer long textual content fields
        for k in ("content", "text", "article", "body", "html"):
            if k in data and data[k]:
                out["content"] = data[k]
                break
        # fallback: put entire JSON as text
        if "content" not in out:
            out["content"] = str(data)
    else:
        out["content"] = str(data)

    try:
        logger.info("Tavily.extract content for %s: title=%s len=%d", url, out.get("title"), len(out.get("content") or ""))
    except Exception:
        pass

    return out
