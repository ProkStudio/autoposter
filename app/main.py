from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.callbacks import register_callbacks
from app.bot.handlers import register_dynamic_handlers, router as handlers_router
from app.config import Settings
from app.db.session import build_engine, build_session_factory
from app.logging import setup_logging
from app.providers.llm import GeminiProvider
from app.providers.matches import MockMatchProvider
from app.services.generation import PredictionGeneratorService
from app.services.moderation import ModerationService
from app.services.publication import PublicationService
from app.services.retention import RetentionService
from app.scheduler.jobs import setup_scheduler


async def build_app() -> tuple[Dispatcher, AsyncIOScheduler, Bot]:
    settings = Settings()
    setup_logging()
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(handlers_router)

    engine = build_engine(settings)
    session_factory = build_session_factory(engine)

    async def force_generate() -> int:
        async with session_factory() as session:
            from app.db.repositories import MatchRepository, PredictionRepository

            service = PredictionGeneratorService(
                match_provider=MockMatchProvider(),
                llm_provider=GeminiProvider(settings),
                match_repo=MatchRepository(session),
                prediction_repo=PredictionRepository(session),
            )
            generated = await service.generate_daily_drafts(settings.max_drafts_per_day)
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

    admin_ids = set(settings.telegram_admin_ids)
    register_dynamic_handlers(dp, admin_ids, queue_getter, stats_getter, force_generate)
    register_callbacks(dp, approve_publish, reject_prediction, admin_ids)

    async def scheduled_generate() -> None:
        async with session_factory() as session:
            from app.db.repositories import MatchRepository, PredictionRepository

            service = PredictionGeneratorService(
                match_provider=MockMatchProvider(),
                llm_provider=GeminiProvider(settings),
                match_repo=MatchRepository(session),
                prediction_repo=PredictionRepository(session),
            )
            await service.generate_daily_drafts(settings.max_drafts_per_day)
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
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
