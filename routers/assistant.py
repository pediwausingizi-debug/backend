# routers/assistant.py

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["assistant"])


class ChatRequest(BaseModel):
    message: str


def _extract_generated_text(data) -> str:
    """
    Hugging Face Inference API commonly returns:
      - [{"generated_text": "..."}]  (text-generation)
      - {"generated_text": "..."}    (some pipelines)
      - {"error": "..."} / {"estimated_time": ...} (errors / loading)
    """
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0].get("generated_text") or str(data)

    if isinstance(data, dict):
        return (
            data.get("generated_text")
            or data.get("summary_text")
            or data.get("translation_text")
            or str(data)
        )

    return str(data)


@router.post("/chat")
async def chat_free(payload: ChatRequest):
    text = (payload.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message required")

    token = os.getenv("HF_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Missing HF_API_TOKEN in environment")

    # Use a reasonably reliable serverless-friendly model.
    # If you want a different one, swap the model id below.
    model_id = os.getenv("HF_MODEL_ID", "HuggingFaceH4/zephyr-7b-beta")
    api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"


    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Simple instruct-style prompt to improve chat behavior on many models
    prompt = f"### Instruction:\n{text}\n\n### Response:\n"

    payload_body = {
        "inputs": prompt,
        "options": {"wait_for_model": True},
        # You can uncomment these if you want more control; model-dependent:
        # "parameters": {"max_new_tokens": 256, "temperature": 0.7, "return_full_text": False},
    }

    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(api_url, headers=headers, json=payload_body)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="HF request timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"HF request error: {str(e)}")

    if resp.status_code != 200:
        # Return the upstream reason (trimmed) instead of a generic 500.
        # This makes debugging (401/403/429/503/etc) much easier.
        raise HTTPException(
            status_code=502,
            detail=f"HF error {resp.status_code}: {resp.text[:400]}",
        )

    data = resp.json()
    reply = _extract_generated_text(data)

    return {
        "reply": reply,
        "model": model_id,
    }
