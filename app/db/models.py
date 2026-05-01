from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import HitMiss, MatchOutcome, PredictionStatus


class MatchModel(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("provider_match_id", name="uq_provider_match_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_match_id: Mapped[str] = mapped_column(String(128), nullable=False)
    league: Mapped[str] = mapped_column(String(128), nullable=False)
    home_team: Mapped[str] = mapped_column(String(128), nullable=False)
    away_team: Mapped[str] = mapped_column(String(128), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class PredictionModel(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("match_id", name="uq_prediction_match"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[PredictionStatus] = mapped_column(
        Enum(PredictionStatus), default=PredictionStatus.DRAFT, nullable=False
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[MatchOutcome] = mapped_column(Enum(MatchOutcome), nullable=False)
    total_line: Mapped[float] = mapped_column(Float, nullable=False)
    total_direction: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    moderation_message_id: Mapped[int | None] = mapped_column(nullable=True)
    channel_message_id: Mapped[int | None] = mapped_column(nullable=True)
    hit_miss: Mapped[HitMiss] = mapped_column(
        Enum(HitMiss), default=HitMiss.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MatchResultModel(Base):
    __tablename__ = "match_results"
    __table_args__ = (UniqueConstraint("match_id", name="uq_result_match"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(nullable=False)
    home_goals: Mapped[int] = mapped_column(Integer, nullable=False)
    away_goals: Mapped[int] = mapped_column(Integer, nullable=False)
    confirmed_by_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
