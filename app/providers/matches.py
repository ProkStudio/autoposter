from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

import httpx

from app.domain.entities import Match


class MatchProvider(Protocol):
    async def get_upcoming_matches(self) -> list[Match]:
        """Return upcoming football matches."""


class MockMatchProvider:
    async def get_upcoming_matches(self) -> list[Match]:
        now = datetime.now(timezone.utc)
        batch_id = int(now.timestamp())
        matches: list[Match] = []
        for idx in range(1, 11):
            matches.append(
                Match(
                    provider_match_id=f"mock-{batch_id}-{idx}",
                    league="Mock Premier League",
                    home_team=f"Team {idx}A",
                    away_team=f"Team {idx}B",
                    starts_at=now + timedelta(hours=idx + 2),
                )
            )
        return matches


class OpenLigaDBMatchProvider:
    """Fetches upcoming real matches from OpenLigaDB."""

    def __init__(self, leagues: list[str] | None = None) -> None:
        self.base_url = "https://api.openligadb.de/getmatchdata"
        self.leagues = leagues or ["bl1", "bl2", "bl3"]

    async def get_upcoming_matches(self) -> list[Match]:
        now = datetime.now(timezone.utc)
        matches: list[Match] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for league in self.leagues:
                try:
                    response = await client.get(f"{self.base_url}/{league}")
                    response.raise_for_status()
                    payload = response.json()
                except Exception:
                    continue

                for item in payload:
                    starts_at = self._parse_datetime(item.get("MatchDateTimeUTC"))
                    if starts_at is None or starts_at <= now:
                        continue
                    team1 = (item.get("Team1") or {}).get("TeamName")
                    team2 = (item.get("Team2") or {}).get("TeamName")
                    if not team1 or not team2:
                        continue
                    provider_id = item.get("MatchID")
                    if provider_id is None:
                        continue
                    matches.append(
                        Match(
                            provider_match_id=f"openligadb-{provider_id}",
                            league=item.get("LeagueName") or league.upper(),
                            home_team=team1,
                            away_team=team2,
                            starts_at=starts_at,
                        )
                    )
        return sorted(matches, key=lambda m: m.starts_at)

    @staticmethod
    def _parse_datetime(raw: str | None) -> datetime | None:
        if not raw:
            return None
        value = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
