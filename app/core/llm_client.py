import httpx
import os
from app.config import settings

API_URL = "https://openrouter.ai/api/v1/chat/completions"

def llm_completion(prompt: str, model=None, json_mode=False):
    messages = [{"role": "system", "content": prompt}]
    payload = {
        "model": model or settings.openrouter_model,
        "messages": messages
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json"
    }
    resp = httpx.post(API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    return text
