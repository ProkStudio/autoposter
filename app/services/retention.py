from app.db.repositories import PredictionRepository


class RetentionService:
    def __init__(self, prediction_repo: PredictionRepository) -> None:
        self.prediction_repo = prediction_repo

    async def cleanup(self, days: int = 90) -> int:
        return await self.prediction_repo.cleanup_older_than(days)
