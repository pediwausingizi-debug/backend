import os
from google import genai

GEMINI_MODEL_VISION = os.getenv("GEMINI_MODEL_VISION", "gemini-3-flash-preview")


def analyze_farm_image_bytes(
    image_bytes: bytes,
    mime_type: str,
    note: str | None = None,
) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an agricultural image assistant for a farm management app.

Analyze the uploaded image and respond in a practical way for a farmer.

Focus on:
1. What is visibly noticeable in the image
2. Possible disease / issue / abnormality if any
3. Confidence note: low, medium, or high
4. Immediate recommended actions
5. When the farmer should consult a vet or agronomist

Rules:
- Do not claim certainty if the image is unclear.
- If the image is not about farming, say so clearly.
- If the image quality is poor, say that clearly.
- Keep the answer concise and practical.
- Return plain text only.

Additional note from user:
{note or "No additional note provided."}
""".strip()

    response = client.models.generate_content(
        model=GEMINI_MODEL_VISION,
        contents=[
            prompt,
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_bytes,
                }
            },
        ],
    )

    text = getattr(response, "text", None)
    if not text:
        text = "I could not analyze this image clearly."

    return {
        "reply": text.strip(),
        "note": note or "",
        "mime_type": mime_type,
    }