from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MatchModel, MatchResultModel, PredictionModel
from app.domain.enums import HitMiss, PredictionStatus


class MatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_match(
        self, provider_match_id: str, league: str, home_team: str, away_team: str, starts_at: datetime
    ) -> MatchModel:
        existing = await self.session.scalar(
            select(MatchModel).where(MatchModel.provider_match_id == provider_match_id)
        )
        if existing:
            existing.starts_at = starts_at
            existing.league = league
            existing.home_team = home_team
            existing.away_team = away_team
            return existing
        match = MatchModel(
            provider_match_id=provider_match_id,
            league=league,
            home_team=home_team,
            away_team=away_team,
            starts_at=starts_at,
        )
        self.session.add(match)
        await self.session.flush()
        return match


class PredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists_for_match(self, match_id: int) -> bool:
        return (
            await self.session.scalar(
                select(func.count(PredictionModel.id)).where(PredictionModel.match_id == match_id)
            )
            > 0
        )

    async def count_created_today(self, now: datetime) -> int:
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(
            await self.session.scalar(
                select(func.count(PredictionModel.id)).where(PredictionModel.created_at >= day_start)
            )
            or 0
        )

    async def create_draft(
        self,
        match_id: int,
        full_text: str,
        outcome: str,
        total_line: float,
        total_direction: str,
        confidence: int,
    ) -> PredictionModel:
        draft = PredictionModel(
            match_id=match_id,
            full_text=full_text,
            outcome=outcome,
            total_line=total_line,
            total_direction=total_direction,
            confidence=confidence,
            status=PredictionStatus.DRAFT,
        )
        self.session.add(draft)
        await self.session.flush()
        return draft

    async def get_queue(self) -> list[PredictionModel]:
        result = await self.session.scalars(
            select(PredictionModel).where(PredictionModel.status == PredictionStatus.SENT_TO_MODERATION)
        )
        return list(result)

    async def get_by_id(self, prediction_id: int) -> PredictionModel | None:
        return await self.session.get(PredictionModel, prediction_id)

    async def set_status(self, prediction_id: int, status: PredictionStatus) -> None:
        await self.session.execute(
            update(PredictionModel).where(PredictionModel.id == prediction_id).values(status=status)
        )

    async def mark_published(self, prediction_id: int, channel_message_id: int) -> None:
        await self.session.execute(
            update(PredictionModel)
            .where(PredictionModel.id == prediction_id)
            .values(
                status=PredictionStatus.PUBLISHED,
                channel_message_id=channel_message_id,
                published_at=datetime.utcnow(),
            )
        )

    async def stats(self, days: int) -> dict[str, int]:
        since = datetime.utcnow() - timedelta(days=days)
        rows = await self.session.execute(
            select(PredictionModel.hit_miss, func.count(PredictionModel.id))
            .where(PredictionModel.created_at >= since)
            .group_by(PredictionModel.hit_miss)
        )
        out = {"hit": 0, "miss": 0, "pending": 0}
        for hit_miss, count in rows:
            if hit_miss == HitMiss.HIT:
                out["hit"] = count
            elif hit_miss == HitMiss.MISS:
                out["miss"] = count
            else:
                out["pending"] = count
        return out

    async def cleanup_older_than(self, days: int) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            delete(PredictionModel).where(PredictionModel.created_at < cutoff)
        )
        return int(result.rowcount or 0)


class ResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_result(
        self, match_id: int, home_goals: int, away_goals: int, confirmed_by_admin: bool
    ) -> MatchResultModel:
        existing = await self.session.scalar(
            select(MatchResultModel).where(MatchResultModel.match_id == match_id)
        )
        if existing:
            existing.home_goals = home_goals
            existing.away_goals = away_goals
            existing.confirmed_by_admin = confirmed_by_admin
            return existing
        result = MatchResultModel(
            match_id=match_id,
            home_goals=home_goals,
            away_goals=away_goals,
            confirmed_by_admin=confirmed_by_admin,
        )
        self.session.add(result)
        await self.session.flush()
        return result
