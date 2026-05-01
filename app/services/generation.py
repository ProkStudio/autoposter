from __future__ import annotations

from datetime import datetime, timezone
from random import choice, randint, uniform

from app.db.repositories import MatchRepository, PredictionRepository
from app.domain.entities import Match, PredictionDraft
from app.domain.enums import MatchOutcome
from app.providers.llm import LLMProvider
from app.providers.matches import MatchProvider


class PredictionGeneratorService:
    """Generates and stores drafts based on upcoming matches."""

    def __init__(
        self,
        match_provider: MatchProvider,
        llm_provider: LLMProvider,
        match_repo: MatchRepository,
        prediction_repo: PredictionRepository,
        custom_prompt: str | None = None,
    ) -> None:
        self.match_provider = match_provider
        self.llm_provider = llm_provider
        self.match_repo = match_repo
        self.prediction_repo = prediction_repo
        self.custom_prompt = custom_prompt

    async def generate_daily_drafts(self, max_drafts_per_day: int, force: bool = False) -> list[int]:
        already = await self.prediction_repo.count_created_today(datetime.now(timezone.utc))
        if not force and already >= max_drafts_per_day:
            return []

        matches = await self.match_provider.get_upcoming_matches()
        available_slots = max_drafts_per_day if force else max_drafts_per_day - already
        selected = self._select_matches(matches)[:available_slots]

        created_ids: list[int] = []
        for match in selected:
            db_match = await self.match_repo.upsert_match(
                provider_match_id=match.provider_match_id,
                league=match.league,
                home_team=match.home_team,
                away_team=match.away_team,
                starts_at=match.starts_at,
            )
            if await self.prediction_repo.exists_for_match(db_match.id):
                continue
            draft = await self.generate_text(match)
            prediction = await self.prediction_repo.create_draft(
                match_id=db_match.id,
                full_text=draft.full_text,
                outcome=draft.outcome.value,
                total_line=draft.total_line,
                total_direction=draft.total_direction,
                confidence=draft.confidence,
            )
            created_ids.append(prediction.id)
        return created_ids

    def _select_matches(self, matches: list[Match]) -> list[Match]:
        return sorted(matches, key=lambda m: m.starts_at)[:10]

    async def generate_text(self, match: Match) -> PredictionDraft:
        outcome = choice([MatchOutcome.HOME_WIN, MatchOutcome.DRAW, MatchOutcome.AWAY_WIN])
        total_line = round(uniform(1.5, 3.5), 1)
        total_direction = choice(["over", "under"])
        confidence = randint(55, 78)

        base_instruction = (
            self.custom_prompt.strip()
            if self.custom_prompt and self.custom_prompt.strip()
            else (
                "Составь пост на русском о футбольном матче в стиле спортивного аналитика. "
                "Структура: громкий заголовок, матч, прогноз (исход + тотал), короткий разбор, "
                "уверенность в процентах. Без дисклеймера."
            )
        )
        # Always pass concrete match context even with a custom prompt.
        prompt = (
            f"{base_instruction}\n\n"
            "Обязательные данные матча (используй их буквально):\n"
            f"- Home team: {match.home_team}\n"
            f"- Away team: {match.away_team}\n"
            f"- League: {match.league}\n"
            f"- Kickoff (UTC): {match.starts_at.isoformat()}\n"
        )
        llm_text = await self.llm_provider.generate(prompt)
        if not llm_text.strip():
            outcome_label = {
                MatchOutcome.HOME_WIN: "П1",
                MatchOutcome.DRAW: "X",
                MatchOutcome.AWAY_WIN: "П2",
            }[outcome]
            total_label = "ТБ" if total_direction == "over" else "ТМ"
            llm_text = (
                f"🔥 {match.home_team} — {match.away_team}\n"
                f"🏆 {match.league}\n\n"
                "Разбор без воды:\n"
                f"- {match.home_team} дома играет агрессивнее и чаще доводит атаки до удара.\n"
                f"- {match.away_team} регулярно оставляет зоны между линиями при высоком темпе.\n"
                "- Матч выглядит как игра с моментами, а не закрытый шахматный сценарий.\n\n"
                "✅ Ставка на матч:\n"
                f"- Основная: {outcome_label}\n"
                f"- Дополнительно: {total_label} {total_line}\n\n"
                f"📊 Уверенность: {confidence}%\n"
                "Забираем по линии до просадки коэффициента."
            )

        return PredictionDraft(
            title=f"{match.home_team} vs {match.away_team}",
            outcome=outcome,
            total_line=total_line,
            total_direction=total_direction,
            confidence=confidence,
            rationale="See generated text.",
            disclaimer="Not financial advice.",
            full_text=llm_text,
        )
