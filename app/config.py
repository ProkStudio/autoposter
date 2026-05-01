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
    telegram_admin_ids: list[int] = Field(alias="TELEGRAM_ADMIN_IDS")
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

    post_fixed_times: list[time] = Field(alias="POST_FIXED_TIMES")
    prematch_window_hours: list[int] = Field(alias="PREMATCH_WINDOW_HOURS")
    max_drafts_per_day: int = Field(default=3, alias="MAX_DRAFTS_PER_DAY")
    llm_provider: Literal["gemini"] = "gemini"

    @field_validator("telegram_admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list):
            return value
        return [int(item.strip()) for item in value.split(",") if item.strip()]

    @field_validator("post_fixed_times", mode="before")
    @classmethod
    def parse_times(cls, value: str | list[time]) -> list[time]:
        if isinstance(value, list):
            return value
        parsed: list[time] = []
        for item in value.split(","):
            hours, minutes = item.strip().split(":")
            parsed.append(time(hour=int(hours), minute=int(minutes)))
        return parsed

    @field_validator("prematch_window_hours", mode="before")
    @classmethod
    def parse_windows(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list):
            return value
        return [int(item.strip()) for item in value.split(",") if item.strip()]

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
