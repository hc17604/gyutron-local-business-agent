from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import settings


PROVIDERS = [
    {
        "id": "openai_compatible",
        "label": "OpenAI-compatible",
        "default_base_url": "https://api.openai.com/v1",
        "requires_api_key": True,
    },
    {"id": "openai", "label": "OpenAI", "default_base_url": "https://api.openai.com/v1", "requires_api_key": True},
    {"id": "deepseek", "label": "DeepSeek", "default_base_url": "https://api.deepseek.com/v1", "requires_api_key": True},
    {"id": "custom", "label": "Custom", "default_base_url": "http://localhost:8001/v1", "requires_api_key": False},
    {"id": "ollama", "label": "Ollama", "default_base_url": "http://localhost:11434/v1", "requires_api_key": False},
    {"id": "lm_studio", "label": "LM Studio", "default_base_url": "http://localhost:1234/v1", "requires_api_key": False},
]


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model_name: str


def provider_default_base_url(provider: str) -> str:
    for item in PROVIDERS:
        if item["id"] == provider:
            return item["default_base_url"]
    return "http://localhost:8001/v1"


class LLMAdapter:
    def __init__(self, config: LLMConfig):
        self.config = config

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        base_url = self.config.base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            raise ValueError("Model response did not include choices.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise ValueError("Model response did not include message content.")
        return str(content)
