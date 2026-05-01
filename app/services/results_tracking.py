from __future__ import annotations

from app.db.repositories import PredictionRepository, ResultRepository
from app.domain.enums import HitMiss, MatchOutcome
from app.providers.results import ResultProvider


class ResultsTrackingService:
    def __init__(
        self,
        result_provider: ResultProvider,
        prediction_repo: PredictionRepository,
        result_repo: ResultRepository,
    ) -> None:
        self.result_provider = result_provider
        self.prediction_repo = prediction_repo
        self.result_repo = result_repo

    async def sync_result(self, match_id: int) -> bool:
        result = await self.result_provider.get_result(match_id)
        if result is None:
            return False
        await self.result_repo.upsert_result(
            match_id=result.match_id,
            home_goals=result.home_goals,
            away_goals=result.away_goals,
            confirmed_by_admin=False,
        )
        return True

    @staticmethod
    def evaluate_hit(outcome: MatchOutcome, home_goals: int, away_goals: int) -> HitMiss:
        if home_goals > away_goals and outcome == MatchOutcome.HOME_WIN:
            return HitMiss.HIT
        if home_goals == away_goals and outcome == MatchOutcome.DRAW:
            return HitMiss.HIT
        if home_goals < away_goals and outcome == MatchOutcome.AWAY_WIN:
            return HitMiss.HIT
        return HitMiss.MISS
