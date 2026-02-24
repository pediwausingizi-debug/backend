# routers/assistant.py

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["assistant"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat_free(payload: ChatRequest):
    text = (payload.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message required")

    # Keep your env var name, but HF docs often call it HF_TOKEN.
    token = os.getenv("HF_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Missing HF_API_TOKEN in environment")

    # IMPORTANT:
    # Use router OpenAI-compatible endpoint for chat completions
    # and a model that is actually deployed on hf-inference (note the :hf-inference suffix).
    model = os.getenv("HF_MODEL_ID", "HuggingFaceTB/SmolLM3-3B:hf-inference")

    api_url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
        "stream": False,
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
            detail=f"HF error {resp.status_code}: {resp.text[:800]}",
        )

    data = resp.json()

    # OpenAI-compatible response shape:
    # { "choices": [ { "message": { "content": "..." } } ] }
    try:
        reply = data["choices"][0]["message"]["content"]
    except Exception:
        reply = str(data)

    return {"reply": reply, "model": model}
