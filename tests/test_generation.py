import asyncio
from datetime import datetime, timezone

from app.domain.entities import Match
from app.services.generation import PredictionGeneratorService


class DummyLLM:
    async def generate(self, prompt: str) -> str:
        return "Матч: A-B\nПрогноз: home_win + over 2.5\nОбоснование: тест\nУверенность: 66%\nДисклеймер: тест"


class DummyMatchProvider:
    async def get_upcoming_matches(self) -> list[Match]:
        return [
            Match(
                provider_match_id="1",
                league="L",
                home_team="A",
                away_team="B",
                starts_at=datetime.now(timezone.utc),
            )
        ]


class DummyMatchRepo:
    async def upsert_match(self, **kwargs):
        class M:
            id = 1

        return M()


class DummyPredictionRepo:
    async def count_created_today(self, now):
        return 0

    async def exists_for_match(self, match_id: int):
        return False

    async def create_draft(self, **kwargs):
        class P:
            id = 123

        return P()


def test_generate_daily_drafts_creates_one_draft():
    service = PredictionGeneratorService(
        match_provider=DummyMatchProvider(),
        llm_provider=DummyLLM(),
        match_repo=DummyMatchRepo(),
        prediction_repo=DummyPredictionRepo(),
    )
    ids = asyncio.run(service.generate_daily_drafts(max_drafts_per_day=3))
    assert ids == [123]
