from __future__ import annotations

from aiogram import Bot

from app.db.repositories import PredictionRepository
from app.domain.enums import PredictionStatus


class PublicationService:
    def __init__(self, bot: Bot, prediction_repo: PredictionRepository, channel_id: int) -> None:
        self.bot = bot
        self.prediction_repo = prediction_repo
        self.channel_id = channel_id

    async def publish_if_approved(self, prediction_id: int) -> bool:
        prediction = await self.prediction_repo.get_by_id(prediction_id)
        if prediction is None or prediction.status != PredictionStatus.APPROVED:
            return False
        if prediction.channel_message_id:
            return True
        sent = await self.bot.send_message(chat_id=self.channel_id, text=prediction.full_text)
        await self.prediction_repo.mark_published(prediction_id, sent.message_id)
        return True
