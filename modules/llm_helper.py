# modules/llm_helper.py

import os
from typing import List, Optional
import requests
from dotenv import load_dotenv

# Load .env DO NOT REMOVE THIS because settings.py is not imported here
load_dotenv()


def classify_with_deepseek(
    query: str, options: List[str], api_key: Optional[str] = None, timeout: int = 10
) -> str:
    """
    Call Deepseek chat to map `query` to one of the provided `options`.
    Returns exactly one of the options (matching the original casing) when possible,
    otherwise returns the raw model output stripped.

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
        "choose the single best matching label. Respond with exactly one token: the label. "
        "Do not add punctuation, explanation, or any extra text."
    )

    user_prompt = f"Query: \"{query}\"\nOptions: {', '.join(options)}\nReturn only the matching option label."

    # Allow specifying model via env var; default to Deepseek chat model
    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 16,
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

    # Normalize and try to map to one of the provided options (case-insensitive)
    lowered_to_orig = {opt.lower(): opt for opt in options}
    # Also allow matching by token that contains the option (e.g., model might return "PLAYER_STATS\n")
    tokens = [t.strip() for t in content.splitlines() if t.strip()]
    first_token = tokens[0] if tokens else content

    candidate = first_token.strip().lower()
    if candidate in lowered_to_orig:
        return lowered_to_orig[candidate]

    # If exact not found, try to find any option substring in content
    for low_opt, orig_opt in lowered_to_orig.items():
        if low_opt in content.lower():
            return orig_opt

    # As last resort, return raw content
    return content
