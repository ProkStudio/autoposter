from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

from app.domain.entities import Match


class MatchProvider(Protocol):
    async def get_upcoming_matches(self) -> list[Match]:
        """Return upcoming football matches."""


class MockMatchProvider:
    async def get_upcoming_matches(self) -> list[Match]:
        now = datetime.now(timezone.utc)
        matches: list[Match] = []
        for idx in range(1, 11):
            matches.append(
                Match(
                    provider_match_id=f"mock-{idx}",
                    league="Mock Premier League",
                    home_team=f"Team {idx}A",
                    away_team=f"Team {idx}B",
                    starts_at=now + timedelta(hours=idx + 2),
                )
            )
        return matches
