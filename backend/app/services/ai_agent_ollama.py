from typing import Any, Dict, List
import logging
import json
import requests
from app.config import settings

logger = logging.getLogger(__name__)


def call_ollama(prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
    """Call a local Ollama HTTP API and return generated text.

    This wrapper tries multiple possible Ollama endpoints and payload shapes.
    It raises a RuntimeError with collected endpoint errors if none succeed.
    """
    if not settings.OLLAMA_URL or not settings.OLLAMA_MODEL:
        raise RuntimeError("Ollama not configured: set OLLAMA_URL and OLLAMA_MODEL")

    base = settings.OLLAMA_URL.rstrip("/")
    model = settings.OLLAMA_MODEL

    endpoints: List[str] = ["/api/generate", "/v1/generate", "/generate", "/v1/responses", ""]

    def _try_with_model(candidate_model: str) -> str | None:
        """Attempt generation using candidate_model. Returns text on success, None on failure.
        Side-effect: collects errors into the outer scope 'errors' list.
        """
        errors_local: List[str] = []
        for ep in endpoints:
            url = f"{base}{ep}"

            if ep == "/v1/responses":
                send_payload: Dict[str, Any] = {"model": candidate_model, "input": prompt}
            else:
                send_payload = {"model": candidate_model, "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}

            try:
                resp = requests.post(url, json=send_payload, timeout=12)
            except Exception as e:
                errors_local.append(f"request error for {url}: {e}")
                continue

            if resp.status_code != 200:
                body = None
                try:
                    body = resp.text
                except Exception:
                    body = f"status {resp.status_code}"
                errors_local.append(f"non-200 from {url}: {resp.status_code} - {body}")
                continue

            try:
                data = resp.json()
            except Exception:
                return resp.text

            # parse known shapes
            if isinstance(data, dict):
                if "text" in data and isinstance(data["text"], str):
                    return data["text"]
                if "output" in data and isinstance(data["output"], str):
                    return data["output"]

                if "generations" in data and isinstance(data["generations"], list):
                    parts: List[str] = []
                    for g in data["generations"]:
                        if isinstance(g, dict):
                            for k in ("text", "content"):
                                if k in g and isinstance(g[k], str):
                                    parts.append(g[k])
                    if parts:
                        return "\n".join(parts)

                if "choices" in data and isinstance(data["choices"], list):
                    choices = [ch.get("text") for ch in data["choices"] if isinstance(ch, dict) and ch.get("text")]
                    if choices:
                        return "\n".join(choices)

                if "results" in data and isinstance(data["results"], list):
                    texts = [str(r.get("text") or r.get("output") or "") for r in data["results"]]
                    return "\n".join([t for t in texts if t])

                if "output" in data and isinstance(data["output"], list):
                    texts: List[str] = []
                    for out in data["output"]:
                        if isinstance(out, dict):
                            content = out.get("content") or out.get("response")
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict):
                                        if "text" in c and isinstance(c["text"], str):
                                            texts.append(c["text"])
                                        elif "message" in c and isinstance(c["message"], str):
                                            texts.append(c["message"])
                            elif isinstance(content, str):
                                texts.append(content)
                    if texts:
                        return "\n".join(texts)

            try:
                return json.dumps(data)
            except Exception:
                return str(data)

        # attach local errors to outer 'errors' for debugging
        errors.extend(errors_local)
        return None

    # First try with configured model
    errors: List[str] = []
    result = _try_with_model(model)
    if result:
        try:
                logger.info("Ollama.call_ollama successful response (truncated): %s", str(result)[:1000])
        except Exception:
            pass
        return result

    # If failure looks like a missing-model error, try to query /v1/models and retry
    try:
        models_ep = f"{base}/v1/models"
        resp = requests.get(models_ep, timeout=6)
        if resp.status_code == 200:
            try:
                md = resp.json()
                # md may be {'object':'list','data':[{'id': 'llama3.1:8b',...}, ...]}
                candidates = []
                if isinstance(md, dict) and "data" in md and isinstance(md["data"], list):
                    for item in md["data"]:
                        if isinstance(item, dict) and "id" in item:
                            candidates.append(item["id"])
                elif isinstance(md, list):
                    for item in md:
                        if isinstance(item, dict) and "id" in item:
                            candidates.append(item["id"])

                if candidates:
                    # prefer exact library-owned numeric variants, else first
                    chosen = candidates[0]
                    # retry with chosen model
                    retry_result = _try_with_model(chosen)
                    if retry_result:
                        try:
                                logger.info("Ollama.call_ollama retry successful with model %s (truncated): %s", chosen, str(retry_result)[:1000])
                        except Exception:
                            pass
                        return retry_result
                    errors.append(f"retry with model {chosen} failed")
            except Exception as e:
                errors.append(f"failed to parse models response: {e}")
    except Exception as e:
        errors.append(f"failed to list models: {e}")

    # none of the attempts worked
    logger.debug("Ollama.call_ollama failed; errors: %s", errors)
    raise RuntimeError("Ollama: no successful response; errors: " + "; ".join(errors))


def stream_ollama(prompt: str, max_tokens: int = 512, temperature: float = 0.2):
    """Stream tokens/chunks from Ollama. Yields text chunks as they arrive.

    Supports both /api/generate NDJSON streaming and /v1/responses (non-streaming) as a fallback.
    """
    if not settings.OLLAMA_URL or not settings.OLLAMA_MODEL:
        raise RuntimeError("Ollama not configured: set OLLAMA_URL and OLLAMA_MODEL")

    base = settings.OLLAMA_URL.rstrip("/")
    model = settings.OLLAMA_MODEL

    # prefer streaming endpoint
    ndjson_ep = f"{base}/api/generate"
    json_ep = f"{base}/v1/responses"

    # Try NDJSON streaming first
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
    try:
        with requests.post(ndjson_ep, json=payload, stream=True, timeout=30) as resp:
            if resp.status_code == 200:
                logger.debug("Ollama.stream_ollama connected to NDJSON endpoint %s", ndjson_ep)
                # iterate over lines
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    # NDJSON-style: each line is a JSON object
                    try:
                        obj = json.loads(line)
                        try:
                            logger.debug("Ollama.stream_ollama ndjson obj: %s", str(obj)[:1000])
                        except Exception:
                            pass
                        # common key 'response' or 'text'
                        text = None
                        if isinstance(obj, dict):
                            if "response" in obj:
                                text = obj.get("response")
                            elif "text" in obj:
                                text = obj.get("text")
                        if text:
                            yield text
                    except Exception:
                        # if not JSON, yield raw
                        yield line
                return
    except Exception:
        # fall through to JSON endpoint
        pass

    # Fallback to /v1/responses which returns a JSON output array
    try:
        payload2 = {"model": model, "input": prompt}
        resp = requests.post(json_ep, json=payload2, timeout=30)
        if resp.status_code == 200:
            try:
                data = resp.json()
                try:
                        logger.info("Ollama.stream_ollama json endpoint response keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))
                except Exception:
                    pass
                # data may have 'output' list
                if isinstance(data, dict) and "output" in data and isinstance(data["output"], list):
                    for item in data["output"]:
                        if isinstance(item, dict):
                            # look for text content
                            if item.get("type") == "message" and isinstance(item.get("content"), list):
                                for c in item.get("content"):
                                    if isinstance(c, dict) and c.get("type") == "output_text":
                                        t = c.get("text")
                                        if t:
                                            yield t
                            elif isinstance(item.get("text"), str):
                                yield item.get("text")
                # final fallback: try top-level 'text' key
                if isinstance(data, dict) and "text" in data and isinstance(data["text"], str):
                    yield data["text"]
            except Exception:
                yield resp.text
            return
    except Exception:
        pass

    raise RuntimeError("Ollama streaming failed: no reachable streaming or JSON endpoints")

