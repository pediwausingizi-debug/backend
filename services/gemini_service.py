import os
from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def build_farm_context(summary: dict, recommendations: dict, predictions: dict) -> str:
    top_recs = recommendations.get("all", [])[:5]
    top_animal_preds = predictions.get("animals", [])[:3]
    top_crop_preds = predictions.get("crops", [])[:3]
    finance_pred = predictions.get("finance", {})

    rec_lines = []
    for item in top_recs:
        rec_lines.append(
            f"- [{item.get('severity', 'info').upper()}] "
            f"{item.get('title')}: {item.get('message')}"
        )

    animal_pred_lines = []
    for item in top_animal_preds:
        animal_name = (
            item.get("name")
            or item.get("tag_number")
            or f"Animal #{item.get('animal_id')}"
        )
        animal_pred_lines.append(
            f"- {animal_name}: predicted monthly income "
            f"{float(item.get('predicted_monthly_income', 0) or 0):.2f}"
        )

    crop_pred_lines = []
    for item in top_crop_preds:
        crop_name = item.get("crop_name") or f"Crop Cycle #{item.get('crop_cycle_id')}"
        plot_name = item.get("plot_name") or "Unknown Plot"
        crop_pred_lines.append(
            f"- {crop_name} in {plot_name}: predicted cycle income "
            f"{float(item.get('predicted_cycle_income', 0) or 0):.2f}"
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
- Total income: {float(summary.get("total_income", 0) or 0):.2f}
- Total expenses: {float(summary.get("total_expenses", 0) or 0):.2f}
- Net profit: {float(summary.get("net_profit", 0) or 0):.2f}
- Summary: {summary.get("summary", "")}

TOP RECOMMENDATIONS
{chr(10).join(rec_lines) if rec_lines else "- No recommendations available yet."}

FINANCE PREDICTIONS
- Predicted monthly revenue: {float(finance_pred.get("predicted_monthly_revenue", 0) or 0):.2f}
- Predicted monthly expenses: {float(finance_pred.get("predicted_monthly_expenses", 0) or 0):.2f}
- Predicted net profit: {float(finance_pred.get("predicted_net_profit", 0) or 0):.2f}
- Method: {finance_pred.get("method", "unknown")}

TOP ANIMAL PREDICTIONS
{chr(10).join(animal_pred_lines) if animal_pred_lines else "- No animal predictions available yet."}

TOP CROP PREDICTIONS
{chr(10).join(crop_pred_lines) if crop_pred_lines else "- No crop predictions available yet."}
""".strip()


def format_history(history: list | None) -> str:
    if not history:
        return "No previous conversation."

    lines = []

    for item in history[-8:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role", "user")
        text = item.get("text", "")

        if text:
            lines.append(f"{str(role).upper()}: {text}")

    return "\n".join(lines) if lines else "No previous conversation."


def generate_chat_reply(
    user_message: str,
    summary: dict,
    recommendations: dict,
    predictions: dict,
    history: list | None = None,
) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)

    system_context = build_farm_context(summary, recommendations, predictions)
    conversation_history = format_history(history)

    system_prompt = f"""
{system_context}

INSTRUCTIONS
- Answer using the farm data above.
- Use recent conversation only for context.
- Do not invent farm records that are not provided.
- Be useful and direct.
- Mention profitability, expenses, risks, or next actions when relevant.
- If the user asks about image/disease diagnosis from a photo, say image analysis is currently unavailable.
- Keep the answer under 180 words.
""".strip()

    user_prompt = f"""
RECENT CONVERSATION
{conversation_history}

USER QUESTION
{user_message}
""".strip()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=350,
    )

    text = response.choices[0].message.content if response.choices else None

    if text:
        return text.strip()

    return "I could not generate a response at the moment."