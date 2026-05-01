from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import MatchOutcome


@dataclass(slots=True)
class Match:
    provider_match_id: str
    league: str
    home_team: str
    away_team: str
    starts_at: datetime


@dataclass(slots=True)
class PredictionDraft:
    title: str
    outcome: MatchOutcome
    total_line: float
    total_direction: str
    confidence: int
    rationale: str
    disclaimer: str
    full_text: str
