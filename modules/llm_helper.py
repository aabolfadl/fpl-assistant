# modules/llm_helper.py

import os
from typing import List, Optional
import requests
from dotenv import load_dotenv

# Load .env DO NOT REMOVE THIS because settings.py is not imported here
load_dotenv()


def classify_with_deepseek(
    query: str, options: List[str], api_key: Optional[str] = None, timeout: int = 10
) -> list:
    """
    Call Deepseek chat to map `query` to up to 3 of the provided `options`.
    Returns a list of up to 3 options (matching the original casing) when possible,
    otherwise returns the raw model output as a list of strings.

    - Reads DEEPSEEK_API_KEY & DEEPSEEK_API_URL from environment.
    """
    if not options:
        raise ValueError("options must be a non-empty list of labels")

    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY not found in environment and no api_key provided"
        )

    endpoint = os.getenv("DEEPSEEK_API_URL")

    system_prompt = (
        "You are a concise classifier. Given a user query related to fantasy premier league and "
        "a list of option labels of cypher queries to be executed to match the user query, "
        "choose up to 3 most relevant labels (comma-separated, no explanation). "
        "Return only the matching option labels, separated by commas. "
        "Do not add punctuation, explanation, or any extra text."
    )

    user_prompt = f"Query: \"{query}\"\nOptions: {', '.join(options)}\nReturn up to 3 matching option labels, comma-separated."

    # Allow specifying model via env var; default to Deepseek chat model
    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 32,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        # Surface network/HTTP errors with context
        raise RuntimeError(f"Deepseek request failed: {exc}") from exc

    # Parse JSON safely
    try:
        data = resp.json()
    except ValueError:
        # Not JSON (unexpected) — fallback to raw text
        data = {"raw_text": resp.text}

    # Try to extract text from common chat API response shapes
    content = ""
    if isinstance(data, dict):
        # OpenAI-like: { "choices": [ { "message": { "content": "..." } } ] }
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            pass

        # Another shape: { "message": "..." } or { "message": { "content": "..." } }
        if not content:
            msg = data.get("message")
            if isinstance(msg, dict):
                content = msg.get("content", "") or msg.get("text", "")
            elif isinstance(msg, str):
                content = msg

        # Some APIs use 'result' or 'response'
        if not content:
            content = data.get("result") or data.get("response") or ""

    # Fallback: raw text
    if not content:
        content = resp.text or ""

    content = content.strip()

    # Split by comma, strip whitespace, filter empty
    tokens = [t.strip() for t in content.split(",") if t.strip()]
    # Map to original casing if possible
    lowered_to_orig = {opt.lower(): opt for opt in options}
    mapped = []
    for token in tokens:
        key = token.lower()
        if key in lowered_to_orig:
            mapped.append(lowered_to_orig[key])
        else:
            # Try substring match
            found = False
            for low_opt, orig_opt in lowered_to_orig.items():
                if low_opt in key:
                    mapped.append(orig_opt)
                    found = True
                    break
            if not found:
                mapped.append(token)
    # Limit to 3
    return mapped[:3]
