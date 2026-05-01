import asyncio

from app.services.retention import RetentionService


class DummyRepo:
    async def cleanup_older_than(self, days: int) -> int:
        return 7 if days == 90 else 0


def test_retention_cleanup_default_days():
    service = RetentionService(prediction_repo=DummyRepo())
    deleted = asyncio.run(service.cleanup())
    assert deleted == 7
