from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class MatchResult:
    match_id: int
    home_goals: int
    away_goals: int


class ResultProvider(Protocol):
    async def get_result(self, match_id: int) -> MatchResult | None:
        """Return result if available, otherwise None."""


class MockResultProvider:
    async def get_result(self, match_id: int) -> MatchResult | None:
        return None
