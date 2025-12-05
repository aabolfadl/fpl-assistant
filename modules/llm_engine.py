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
- When suggesting transfers, mention next fixture difficulty if available.
- Keep output short, analytical, and actionable.

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
        "max_tokens": 512,
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


def _hf_inference_api_call(
    model_id: str,
    user_query: str,
    context_data: Dict[str, Any],
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> str:
    """
    Internal helper to call Hugging Face Inference API for text generation.
    Uses the text-generation task endpoint.

    Args:
        model_id: HF model identifier (e.g., "meta-llama/Llama-3.2-1B-Instruct")
        user_query: User's question
        context_data: Context information for the query
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        Generated text response
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN not found in environment")

    # Prepare context
    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    # Format prompt - simple format for instruction models
    prompt = f"""{BASE_SYSTEM_PROMPT.strip()}

User query: "{user_query}"

Context:
{context_json}

Answer using ONLY the provided context. If the context does not contain the answer, say so.

Answer:"""

    # HF Inference API endpoint
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "return_full_text": False,
        },
        "options": {
            "wait_for_model": True,  # Wait if model is loading
        },
    }

    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        # Check for specific error messages
        try:
            error_data = resp.json() if resp else {}
            error_msg = error_data.get("error", str(exc))
            raise RuntimeError(
                f"HF API request failed for {model_id}: {error_msg}"
            ) from exc
        except:
            raise RuntimeError(f"HF API request failed for {model_id}: {exc}") from exc

    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError(f"Invalid JSON response from HF API: {resp.text}")

    # Handle HF API response format
    if isinstance(data, list) and len(data) > 0:
        # Standard response format: [{"generated_text": "..."}]
        generated_text = data[0].get("generated_text", "")
    elif isinstance(data, dict):
        # Alternative format or error
        if "error" in data:
            raise RuntimeError(f"HF API error: {data['error']}")
        generated_text = data.get("generated_text", "")
    else:
        generated_text = str(data)

    return generated_text.strip()


def gemma_generate_answer(user_query: str, context_data: Dict[str, Any]) -> str:
    """
    Call Hugging Face's Gemma model to generate an answer for `user_query`
    using the provided `context_data`.

    Uses google/gemma-1.1-2b-it (instruction-tuned 2B model) which is available
    on HF's free inference API. Note: Gemma models may not support system prompts.

    - Reads `HF_TOKEN` from environment.

    Args:
        user_query: The user's question
        context_data: Dictionary containing context information

    Returns:
        Generated answer text
    """
    # Placeholder implementation for local development / demo purposes.
    # Returns a short, safe response containing the user query and a
    # serialized context summary instead of calling the HF API.
    if user_query is None:
        raise ValueError("user_query must be provided")

    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    return (
        f"(HF Placeholder answer - Gemma) I received your query: '{user_query}'.\n\n"
        f"Context summary:\n{context_json}\n\n"
        "Note: Gemma model calls are disabled in this environment."
    )


def llama_generate_answer(user_query: str, context_data: Dict[str, Any]) -> str:
    """
    Call Hugging Face's Llama model to generate an answer for `user_query`
    using the provided `context_data`.

    Uses meta-llama/Llama-3.2-1B-Instruct (instruction-tuned 1B model) which
    is available on HF's free inference API. This is a smaller, faster model
    suitable for quick responses.

    - Reads `HF_TOKEN` from environment.

    Args:
        user_query: The user's question
        context_data: Dictionary containing context information

    Returns:
        Generated answer text
    """
    # Placeholder implementation for local development / demo purposes.
    # Returns a short, safe response containing the user query and a
    # serialized context summary instead of calling the HF API.
    if user_query is None:
        raise ValueError("user_query must be provided")

    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    return (
        f"(HF Placeholder answer - Llama) I received your query: '{user_query}'.\n\n"
        f"Context summary:\n{context_json}\n\n"
        "Note: Llama model calls are disabled in this environment."
    )
