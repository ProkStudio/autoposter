from __future__ import annotations

from datetime import time
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_channel_id: int = Field(alias="TELEGRAM_CHANNEL_ID")
    telegram_admin_ids_raw: str = Field(alias="TELEGRAM_ADMIN_IDS")
    telegram_moderation_chat_id: int | None = Field(
        default=None, alias="TELEGRAM_MODERATION_CHAT_ID"
    )

    database_url: str = Field(alias="DATABASE_URL")
    tz: str = Field(default="Europe/Moscow", alias="TZ")

    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")

    enable_openrouter_fallback: bool = Field(
        default=False, alias="ENABLE_OPENROUTER_FALLBACK"
    )
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="deepseek/deepseek-chat-v3-0324:free", alias="OPENROUTER_MODEL"
    )
    openrouter_fallback_model: str = Field(
        default="meta-llama/llama-3.1-8b-instruct:free",
        alias="OPENROUTER_FALLBACK_MODEL",
    )
    openrouter_enable_web_search: bool = Field(
        default=False, alias="OPENROUTER_ENABLE_WEB_SEARCH"
    )
    match_provider: Literal["mock", "openligadb"] = Field(
        default="openligadb", alias="MATCH_PROVIDER"
    )
    openligadb_leagues_raw: str = Field(default="bl1,bl2,bl3", alias="OPENLIGADB_LEAGUES")
    strict_llm_only: bool = Field(default=False, alias="STRICT_LLM_ONLY")

    post_fixed_times_raw: str = Field(alias="POST_FIXED_TIMES")
    prematch_window_hours_raw: str = Field(alias="PREMATCH_WINDOW_HOURS")
    max_drafts_per_day: int = Field(default=3, alias="MAX_DRAFTS_PER_DAY")
    llm_provider: Literal["gemini", "openrouter"] = "gemini"

    @field_validator("telegram_moderation_chat_id", mode="before")
    @classmethod
    def parse_optional_chat_id(cls, value: str | int | None) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        value = value.strip()
        if not value:
            return None
        return int(value)

    @property
    def telegram_admin_ids(self) -> list[int]:
        return [
            int(item.strip())
            for item in self.telegram_admin_ids_raw.split(",")
            if item.strip()
        ]

    @property
    def post_fixed_times(self) -> list[time]:
        parsed: list[time] = []
        for item in self.post_fixed_times_raw.split(","):
            hours, minutes = item.strip().split(":")
            parsed.append(time(hour=int(hours), minute=int(minutes)))
        return parsed

    @property
    def prematch_window_hours(self) -> list[int]:
        return [
            int(item.strip())
            for item in self.prematch_window_hours_raw.split(",")
            if item.strip()
        ]

    @property
    def openligadb_leagues(self) -> list[str]:
        return [item.strip() for item in self.openligadb_leagues_raw.split(",") if item.strip()]
