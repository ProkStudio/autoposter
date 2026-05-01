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


class OpenRouterFallbackProvider:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def generate(self, prompt: str) -> str:
        # TODO: implement OpenRouter calls if fallback is enabled.
        raise NotImplementedError("OpenRouter fallback provider is not implemented yet.")
