import os
from typing import Optional
from google import genai

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")


def build_farm_context(summary: dict, recommendations: dict, predictions: dict) -> str:
    top_recs = recommendations.get("all", [])[:5]
    top_animal_preds = predictions.get("animals", [])[:3]
    top_crop_preds = predictions.get("crops", [])[:3]
    finance_pred = predictions.get("finance", {})

    rec_lines = []
    for item in top_recs:
        rec_lines.append(f"- [{item.get('severity', 'info').upper()}] {item.get('title')}: {item.get('message')}")

    animal_pred_lines = []
    for item in top_animal_preds:
        animal_name = item.get("name") or item.get("tag_number") or f"Animal #{item.get('animal_id')}"
        animal_pred_lines.append(
            f"- {animal_name}: predicted monthly income {item.get('predicted_monthly_income', 0):.2f}"
        )

    crop_pred_lines = []
    for item in top_crop_preds:
        crop_name = item.get("crop_name") or f"Crop Cycle #{item.get('crop_cycle_id')}"
        plot_name = item.get("plot_name") or "Unknown Plot"
        crop_pred_lines.append(
            f"- {crop_name} in {plot_name}: predicted cycle income {item.get('predicted_cycle_income', 0):.2f}"
        )

    return f"""
You are FarmXpat AI, an agricultural assistant for a farm management system.
Be practical, concise, and specific. Do not invent farm records that are not provided.
If there is insufficient data, say so clearly and suggest what records the farmer should add.

FARM SUMMARY
- Farm ID: {summary.get("farm_id")}
- Animals tracked: {summary.get("animals_tracked", 0)}
- Plots tracked: {summary.get("plots_tracked", 0)}
- Crop cycles tracked: {summary.get("crop_cycles_tracked", 0)}
- Total income: {summary.get("total_income", 0):.2f}
- Total expenses: {summary.get("total_expenses", 0):.2f}
- Net profit: {summary.get("net_profit", 0):.2f}
- Summary: {summary.get("summary", "")}

TOP RECOMMENDATIONS
{chr(10).join(rec_lines) if rec_lines else "- No recommendations available yet."}

FINANCE PREDICTIONS
- Predicted monthly revenue: {finance_pred.get("predicted_monthly_revenue", 0):.2f}
- Predicted monthly expenses: {finance_pred.get("predicted_monthly_expenses", 0):.2f}
- Predicted net profit: {finance_pred.get("predicted_net_profit", 0):.2f}
- Method: {finance_pred.get("method", "unknown")}

TOP ANIMAL PREDICTIONS
{chr(10).join(animal_pred_lines) if animal_pred_lines else "- No animal predictions available yet."}

TOP CROP PREDICTIONS
{chr(10).join(crop_pred_lines) if crop_pred_lines else "- No crop predictions available yet."}
""".strip()


def generate_chat_reply(user_message: str, summary: dict, recommendations: dict, predictions: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    system_context = build_farm_context(summary, recommendations, predictions)

    prompt = f"""
{system_context}

USER QUESTION
{user_message}

INSTRUCTIONS
- Answer using the farm data above.
- Be useful and direct.
- When relevant, mention profitability, expenses, risks, or next actions.
- If the user asks about disease from an image, tell them image analysis is handled separately.
- Keep the answer under 180 words.
""".strip()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    text = getattr(response, "text", None)
    if text:
        return text.strip()

    return "I could not generate a response at the moment."