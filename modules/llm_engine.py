# modules/llm_engine.py

import os
import json
from typing import Any, Dict
import requests
from dotenv import load_dotenv

# Load .env DO NOT REMOVE THIS because settings.py is not imported here
load_dotenv()


BASE_SYSTEM_PROMPT = """
You are an elite Fantasy Premier League (FPL) analyst. Your job is to answer
the user's question using ONLY the data provided in the context below.

Rules:
- Do NOT guess or hallucinate.
- If the context does not contain the answer, say so.
- Keep output concise, analytical, and actionable.
- At the end of every response, seamlessly suggest one relevant suggested follow-up question the user might ask.


Now read the context carefully.
"""


def deepseek_generate_answer(user_query: str, context_data: Dict[str, Any]) -> str:
    """
    Call Deepseek chat to generate an answer for `user_query` using the provided
    `context_data`. Behavior mirrors `classify_with_deepseek` in terms of
    HTTP handling and response parsing but uses `BASE_SYSTEM_PROMPT` as the
    system prompt and returns the model's text answer.

    - Reads `DEEPSEEK_API_KEY` and `DEEPSEEK_API_URL` from environment.
    """
    if user_query is None:
        raise ValueError("user_query must be provided")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not found in environment")

    endpoint = os.getenv("DEEPSEEK_API_URL")

    # Prepare prompts
    system_prompt = BASE_SYSTEM_PROMPT.strip()
    # Serialize context data for the model; fall back to str() on failure
    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    user_prompt = (
        f'User query: "{user_query}"\n\n'
        f"Context:\n{context_json}\n\n"
        "Answer using ONLY the provided context. If the context does not contain the answer, say so."
    )

    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Deepseek request failed: {exc}") from exc

    try:
        data = resp.json()
    except ValueError:
        data = {"raw_text": resp.text}

    content = ""
    if isinstance(data, dict):
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            pass

        if not content:
            msg = data.get("message")
            if isinstance(msg, dict):
                content = msg.get("content", "") or msg.get("text", "")
            elif isinstance(msg, str):
                content = msg

        if not content:
            content = data.get("result") or data.get("response") or ""

    if not content:
        content = resp.text or ""

    return content.strip()


HF_ENDPOINT = "https://router.huggingface.co/v1/chat/completions"


def _hf_chat_completion(model: str, system_prompt: str, user_prompt: str) -> str:
    """Internal helper for HuggingFace Chat Completions API."""

    api_key = os.getenv("HF_TOKEN")
    if not api_key:
        raise RuntimeError("HF_TOKEN not found in environment")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(HF_ENDPOINT, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"HuggingFace request failed: {exc}") from exc

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return str(data)


def gemma_generate_answer(user_query: str, context_data: Dict[str, Any]) -> str:
    """Generate answer using Gemma via HuggingFace Router Chat API."""
    if user_query is None:
        raise ValueError("user_query must be provided")

    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    user_prompt = (
        f'User query: "{user_query}"\n\n'
        f"Context:\n{context_json}\n\n"
        "Answer using ONLY this context. If context lacks the answer, say so."
    )

    return _hf_chat_completion(
        model="google/gemma-2-2b-it",
        system_prompt=BASE_SYSTEM_PROMPT.strip(),
        user_prompt=user_prompt,
    )


def llama_generate_answer(user_query: str, context_data: Dict[str, Any]) -> str:
    """Generate answer using Llama via HuggingFace Router Chat API."""
    if user_query is None:
        raise ValueError("user_query must be provided")

    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    user_prompt = (
        f'User query: "{user_query}"\n\n'
        f"Context:\n{context_json}\n\n"
        "Answer using ONLY this context. If context lacks the answer, say so."
    )

    return _hf_chat_completion(
        model="meta-llama/Llama-3.2-1B-Instruct",
        system_prompt=BASE_SYSTEM_PROMPT.strip(),
        user_prompt=user_prompt,
    )
