import httpx
from app.core.config import settings

async def explain_with_ai(offer: dict, score: int) -> str | None:
    if not (settings.ai_enabled and settings.ai_api_key and settings.ai_model):
        return None
    endpoint = settings.ai_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.ai_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "Tu aides à évaluer une offre d'alternance informatique. N'invente rien. Réponds en français en deux phrases maximum."},
            {"role": "user", "content": f"Score règles: {score}/100. Offre: {offer}"}
        ]
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(endpoint, json=payload, headers={"Authorization": f"Bearer {settings.ai_api_key}"})
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
