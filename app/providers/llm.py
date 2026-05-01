from __future__ import annotations

import logging
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> str:
        """Generate a prediction text from prompt."""


class GeminiProvider:
    def __init__(self, settings) -> None:
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model

    async def generate(self, prompt: str) -> str:
        if not self._api_key:
            return ""
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception:
            # Never fail update handling because of LLM provider issues.
            logger.exception("Gemini request failed, using template fallback text")
            return ""
        return (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )


class OpenRouterProvider:
    def __init__(
        self,
        api_key: str | None,
        primary_model: str,
        fallback_model: str | None = None,
        enable_web_search: bool = False,
    ) -> None:
        self.api_key = api_key
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.enable_web_search = enable_web_search
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.last_error: str | None = None
        self.last_model_used: str | None = None

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            return ""
        models = [self.primary_model]
        if self.fallback_model and self.fallback_model != self.primary_model:
            models.append(self.fallback_model)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a sports betting content writer for Telegram.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
            }
            if self.enable_web_search:
                payload["plugins"] = [{"id": "web"}]
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(self.url, headers=headers, json=payload)
                    if response.status_code >= 400 and self.enable_web_search:
                        # Some models/providers reject plugin options; retry plain request.
                        fallback_payload = dict(payload)
                        fallback_payload.pop("plugins", None)
                        response = await client.post(
                            self.url, headers=headers, json=fallback_payload
                        )
                    response.raise_for_status()
                    data = response.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if text:
                    self.last_error = None
                    self.last_model_used = model
                    return text
            except Exception:
                logger.exception("OpenRouter request failed for model=%s", model)
                self.last_error = f"model={model}: request failed"
                continue
        return ""
