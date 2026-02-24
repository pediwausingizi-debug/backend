# routers/assistant.py

import os
import re
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["assistant"])


class ChatRequest(BaseModel):
    message: str


# Strip chain-of-thought style wrappers some models emit
_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)
_ANALYSIS_RE = re.compile(r"<analysis>.*?</analysis>\s*", re.DOTALL | re.IGNORECASE)
_REASONING_RE = re.compile(r"<reasoning>.*?</reasoning>\s*", re.DOTALL | re.IGNORECASE)

# Some models use these tags without closing in the expected way; as a fallback, remove open/close tags
_TAG_ONLY_RE = re.compile(r"</?(think|analysis|reasoning)>\s*", re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    text = _THINK_RE.sub("", text)
    text = _ANALYSIS_RE.sub("", text)
    text = _REASONING_RE.sub("", text)
    text = _TAG_ONLY_RE.sub("", text)
    return text.strip()


@router.post("/chat")
async def chat_free(payload: ChatRequest):
    text = (payload.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message required")

    token = os.getenv("HF_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Missing HF_API_TOKEN in environment")

    # Model MUST include provider suffix for HF router OpenAI-compatible endpoint
    model = os.getenv("HF_MODEL_ID", "HuggingFaceTB/SmolLM3-3B:hf-inference")
    if ":" not in model:
        raise HTTPException(
            status_code=500,
            detail="HF_MODEL_ID must include provider suffix, e.g. '...:hf-inference'",
        )

    api_url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Add a system instruction to reduce reasoning output
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Respond with ONLY the final answer. Do not include <think>, analysis, reasoning, or explanations.",
            },
            {"role": "user", "content": text},
        ],
        "stream": False,
        # Optional: you can cap output length if needed
        # "max_tokens": 256,
    }

    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(api_url, headers=headers, json=body)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="HF request timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"HF request error: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"HF error {resp.status_code}: {resp.text[:1200]}",
        )

    data = resp.json()

    try:
        reply = data["choices"][0]["message"]["content"]
    except Exception:
        reply = str(data)

    reply = strip_reasoning(reply)

    return {"reply": reply, "model": model}
