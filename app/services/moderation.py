from __future__ import annotations

from aiogram import Bot

from app.db.repositories import PredictionRepository
from app.domain.enums import PredictionStatus


class ModerationService:
    """Moderation workflow with idempotent status transitions."""

    def __init__(
        self,
        bot: Bot,
        prediction_repo: PredictionRepository,
        moderation_chat_id: int | None,
        admin_ids: set[int],
    ) -> None:
        self.bot = bot
        self.prediction_repo = prediction_repo
        self.moderation_chat_id = moderation_chat_id
        self.admin_ids = admin_ids

    async def send_to_moderation(self, prediction_id: int, text: str) -> int | None:
        prediction = await self.prediction_repo.get_by_id(prediction_id)
        if prediction is None:
            return None
        if prediction.status != PredictionStatus.DRAFT:
            return prediction.moderation_message_id

        recipients = (
            [self.moderation_chat_id]
            if self.moderation_chat_id is not None
            else sorted(self.admin_ids)
        )
        last_message_id: int | None = None
        for recipient in recipients:
            sent = await self.bot.send_message(chat_id=recipient, text=text)
            last_message_id = sent.message_id
        prediction.moderation_message_id = last_message_id
        await self.prediction_repo.set_status(prediction_id, PredictionStatus.SENT_TO_MODERATION)
        return last_message_id

    async def approve(self, prediction_id: int) -> bool:
        prediction = await self.prediction_repo.get_by_id(prediction_id)
        if prediction is None or prediction.status not in (
            PredictionStatus.SENT_TO_MODERATION,
            PredictionStatus.DRAFT,
        ):
            return False
        await self.prediction_repo.set_status(prediction_id, PredictionStatus.APPROVED)
        return True

    async def reject(self, prediction_id: int) -> bool:
        prediction = await self.prediction_repo.get_by_id(prediction_id)
        if prediction is None or prediction.status not in (
            PredictionStatus.SENT_TO_MODERATION,
            PredictionStatus.DRAFT,
        ):
            return False
        await self.prediction_repo.set_status(prediction_id, PredictionStatus.REJECTED)
        return True
