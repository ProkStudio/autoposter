import asyncio

from app.domain.enums import PredictionStatus
from app.services.moderation import ModerationService


class DummyBot:
    async def send_message(self, chat_id: int, text: str):
        class Message:
            message_id = 100

        return Message()


class DummyPrediction:
    def __init__(self, status: PredictionStatus) -> None:
        self.status = status
        self.moderation_message_id = None


class DummyRepo:
    def __init__(self):
        self.pred = DummyPrediction(PredictionStatus.DRAFT)

    async def get_by_id(self, prediction_id: int):
        return self.pred

    async def set_status(self, prediction_id: int, status: PredictionStatus):
        self.pred.status = status


def test_moderation_approve_flow():
    repo = DummyRepo()
    service = ModerationService(
        bot=DummyBot(),
        prediction_repo=repo,
        moderation_chat_id=1,
        admin_ids={1},
    )
    msg_id = asyncio.run(service.send_to_moderation(1, "test"))
    assert msg_id == 100
    assert repo.pred.status == PredictionStatus.SENT_TO_MODERATION

    approved = asyncio.run(service.approve(1))
    assert approved is True
    assert repo.pred.status == PredictionStatus.APPROVED
