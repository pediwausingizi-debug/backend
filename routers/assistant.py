import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from utils.auth_utils import get_current_user  # optional

router = APIRouter(tags=["assistant"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_free(
    payload: ChatRequest,
    # user=Depends(get_current_user),  # optional auth
):
    text = payload.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message required")

    token = os.getenv("HF_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Missing HF API token")

    api_url = "https://api-inference.huggingface.co/models/nousresearch/nous-hermes-13b"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload_body = {
        "inputs": text,
        "options": {"wait_for_model": True},
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(api_url, headers=headers, json=payload_body)

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="HF model failed")

    data = resp.json()
    # The response format depends on the model
    # For regular text models you get `data["generated_text"]`
    reply = data.get("generated_text") or str(data)

    return {"reply": reply}
