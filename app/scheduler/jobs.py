from __future__ import annotations

from datetime import datetime, timedelta
from typing import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import Settings


def setup_scheduler(
    scheduler: AsyncIOScheduler,
    settings: Settings,
    generate_job: Callable[[], Awaitable[None]],
    cleanup_job: Callable[[], Awaitable[None]],
) -> None:
    for post_time in settings.post_fixed_times:
        scheduler.add_job(
            generate_job,
            trigger=CronTrigger(hour=post_time.hour, minute=post_time.minute, timezone=settings.tz),
            id=f"fixed-{post_time.hour}-{post_time.minute}",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    scheduler.add_job(
        cleanup_job,
        trigger=CronTrigger(hour=3, minute=0, timezone=settings.tz),
        id="retention-cleanup",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def within_prematch_window(starts_at: datetime, now: datetime, windows: list[int]) -> bool:
    return any(now + timedelta(hours=low) <= starts_at <= now + timedelta(hours=high) for low, high in [windows])
