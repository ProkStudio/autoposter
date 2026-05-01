from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.callbacks import register_callbacks
from app.bot.handlers import register_dynamic_handlers, router as handlers_router
from app.config import Settings
from app.db.session import build_engine, build_session_factory
from app.logging import setup_logging
from app.domain.enums import PredictionStatus
from app.providers.llm import GeminiProvider, LLMProvider, OpenRouterProvider
from app.providers.matches import MatchProvider, MockMatchProvider, OpenLigaDBMatchProvider
from app.services.generation import PredictionGeneratorService
from app.services.moderation import ModerationService
from app.services.publication import PublicationService
from app.services.retention import RetentionService
from app.scheduler.jobs import setup_scheduler

logger = logging.getLogger(__name__)


async def build_app() -> tuple[Dispatcher, AsyncIOScheduler, Bot]:
    settings = Settings()
    setup_logging()
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(handlers_router)

    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    prompt_key = "custom_generation_prompt"

    def build_llm_provider() -> LLMProvider:
        if settings.enable_openrouter_fallback and settings.openrouter_api_key:
            return OpenRouterProvider(
                api_key=settings.openrouter_api_key,
                primary_model=settings.openrouter_model,
                fallback_model=settings.openrouter_fallback_model,
                enable_web_search=settings.openrouter_enable_web_search,
            )
        return GeminiProvider(settings)

    def build_match_provider() -> MatchProvider:
        if settings.match_provider == "openligadb":
            return OpenLigaDBMatchProvider(settings.openligadb_leagues)
        return MockMatchProvider()

    async def force_generate() -> int:
        async with session_factory() as session:
            from app.db.repositories import MatchRepository, PredictionRepository, SettingsRepository

            settings_repo = SettingsRepository(session)
            service = PredictionGeneratorService(
                match_provider=build_match_provider(),
                llm_provider=build_llm_provider(),
                match_repo=MatchRepository(session),
                prediction_repo=PredictionRepository(session),
                custom_prompt=await settings_repo.get(prompt_key),
                strict_llm_only=settings.strict_llm_only,
            )
            generated = await service.generate_daily_drafts(1, force=True)
            await session.commit()
            return len(generated)

    async def queue_getter() -> list:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            return await PredictionRepository(session).get_queue()

    async def stats_getter(days: int) -> dict[str, int]:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            return await repo.stats(days)

    async def overview_getter() -> dict[str, int]:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            now = datetime.utcnow()
            return {
                "published_total": await repo.published_total(),
                "published_24h": await repo.published_since(now - timedelta(hours=24)),
                "in_moderation": len(await repo.get_by_status(PredictionStatus.SENT_TO_MODERATION)),
                "drafts": len(await repo.get_by_status(PredictionStatus.DRAFT)),
            }

    async def drafts_getter() -> list:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            drafts = await repo.get_by_status(PredictionStatus.DRAFT, limit=10)
            in_moderation = await repo.get_by_status(PredictionStatus.SENT_TO_MODERATION, limit=10)
            approved = await repo.get_by_status(PredictionStatus.APPROVED, limit=10)
            return drafts + in_moderation + approved

    async def set_prompt(value: str | None) -> str:
        async with session_factory() as session:
            from app.db.repositories import SettingsRepository

            repo = SettingsRepository(session)
            if value and value.strip():
                await repo.set(prompt_key, value.strip())
                await session.commit()
                return "Кастомный промпт сохранен."
            await repo.set(prompt_key, "")
            await session.commit()
            return "Промпт сброшен на стандартный."

    async def get_prompt() -> str:
        async with session_factory() as session:
            from app.db.repositories import SettingsRepository

            repo = SettingsRepository(session)
            value = (await repo.get(prompt_key) or "").strip()
            if value:
                return f"Текущий кастомный промпт:\n\n{value}"
            return "Используется стандартный промпт."

    async def status_getter() -> str:
        llm = build_llm_provider()
        provider = "openrouter" if settings.enable_openrouter_fallback else "gemini"
        model = settings.openrouter_model if provider == "openrouter" else settings.gemini_model
        test_ok = False
        try:
            test_text = await llm.generate("Reply with exactly: OK")
            test_ok = bool(test_text.strip())
        except Exception:
            logger.exception("LLM status probe failed")
        web_search = "on" if settings.openrouter_enable_web_search else "off"
        strict_mode = "on" if settings.strict_llm_only else "off"
        return (
            "Status:\n"
            f"- match_provider: {settings.match_provider}\n"
            f"- llm_provider: {provider}\n"
            f"- model: {model}\n"
            f"- openrouter_web_search: {web_search}\n"
            f"- strict_llm_only: {strict_mode}\n"
            f"- llm_probe: {'ok' if test_ok else 'failed'}"
        )

    async def edit_draft(prediction_id: int, new_text: str) -> str:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            ok = await repo.update_full_text(prediction_id, new_text)
            await session.commit()
            if not ok:
                return "Нельзя изменить: не найдено или уже опубликовано."
            return f"Черновик #{prediction_id} обновлен."

    async def delete_draft(prediction_id: int) -> str:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            ok = await repo.delete_prediction(prediction_id)
            await session.commit()
            if not ok:
                return "Нельзя удалить: не найдено или уже опубликовано."
            return f"Черновик #{prediction_id} удален."

    async def approve_publish(prediction_id: int) -> bool:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            moderation_service = ModerationService(
                bot=bot,
                prediction_repo=repo,
                moderation_chat_id=settings.telegram_moderation_chat_id,
                admin_ids=admin_ids,
            )
            publication_service = PublicationService(
                bot=bot,
                prediction_repo=repo,
                channel_id=settings.telegram_channel_id,
            )
            approved = await moderation_service.approve(prediction_id)
            if not approved:
                return False
            await publication_service.publish_if_approved(prediction_id)
            await session.commit()
            return True

    async def reject_prediction(prediction_id: int) -> bool:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            moderation_service = ModerationService(
                bot=bot,
                prediction_repo=PredictionRepository(session),
                moderation_chat_id=settings.telegram_moderation_chat_id,
                admin_ids=admin_ids,
            )
            rejected = await moderation_service.reject(prediction_id)
            await session.commit()
            return rejected

    async def send_to_moderation() -> int:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            moderation_service = ModerationService(
                bot=bot,
                prediction_repo=repo,
                moderation_chat_id=settings.telegram_moderation_chat_id,
                admin_ids=admin_ids,
            )
            drafts = await repo.get_by_status(PredictionStatus.DRAFT, limit=1)
            sent = 0
            for draft in drafts:
                message_id = await moderation_service.send_to_moderation(draft.id, draft.full_text)
                if message_id is not None:
                    sent += 1
            await session.commit()
            return sent

    async def publish_now() -> str:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            repo = PredictionRepository(session)
            moderation_service = ModerationService(
                bot=bot,
                prediction_repo=repo,
                moderation_chat_id=settings.telegram_moderation_chat_id,
                admin_ids=admin_ids,
            )
            publication_service = PublicationService(
                bot=bot,
                prediction_repo=repo,
                channel_id=settings.telegram_channel_id,
            )

            approved = await repo.get_latest_unpublished([PredictionStatus.APPROVED])
            if approved:
                await publication_service.publish_if_approved(approved.id)
                await session.commit()
                return f"Published approved prediction #{approved.id}"

            candidate = await repo.get_latest_unpublished(
                [PredictionStatus.SENT_TO_MODERATION, PredictionStatus.DRAFT]
            )
            if candidate:
                await moderation_service.approve(candidate.id)
                await publication_service.publish_if_approved(candidate.id)
                await session.commit()
                return f"Published prediction #{candidate.id} (fast-track)"

            await session.commit()
            return "No unpublished predictions available."

    admin_ids = set(settings.telegram_admin_ids)
    register_dynamic_handlers(
        dp,
        admin_ids,
        queue_getter,
        status_getter,
        stats_getter,
        force_generate,
        send_to_moderation,
        publish_now,
        overview_getter,
        drafts_getter,
        set_prompt,
        get_prompt,
        edit_draft,
        delete_draft,
    )
    register_callbacks(dp, approve_publish, reject_prediction, admin_ids)

    async def scheduled_generate() -> None:
        async with session_factory() as session:
            from app.db.repositories import MatchRepository, PredictionRepository, SettingsRepository

            settings_repo = SettingsRepository(session)
            service = PredictionGeneratorService(
                match_provider=build_match_provider(),
                llm_provider=build_llm_provider(),
                match_repo=MatchRepository(session),
                prediction_repo=PredictionRepository(session),
                custom_prompt=await settings_repo.get(prompt_key),
                strict_llm_only=settings.strict_llm_only,
            )
            await service.generate_daily_drafts(1)
            await session.commit()

    async def scheduled_cleanup() -> None:
        async with session_factory() as session:
            from app.db.repositories import PredictionRepository

            retention = RetentionService(PredictionRepository(session))
            await retention.cleanup(90)
            await session.commit()

    scheduler = AsyncIOScheduler(timezone=settings.tz)
    setup_scheduler(scheduler, settings, scheduled_generate, scheduled_cleanup)
    return dp, scheduler, bot


async def main() -> None:
    dp, scheduler, bot = await build_app()
    logger.info("Starting scheduler and telegram polling")
    # Ensure polling mode is not blocked by an existing webhook.
    await bot.delete_webhook(drop_pending_updates=False)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Bot polling crashed")
        raise


if __name__ == "__main__":
    asyncio.run(main())
