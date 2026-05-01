from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


def admin_only(admin_ids: set[int], user_id: int) -> bool:
    return user_id in admin_ids


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Football autopost bot is running.")


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "/status - health\n"
        "/queue - moderation queue\n"
        "/stats - hit/miss for 7/30/90 days\n"
        "/force_generate - manually run generation"
    )


@router.message(Command("status"))
async def status(message: Message) -> None:
    await message.answer("OK")


def register_dynamic_handlers(
    dp: Dispatcher,
    admin_ids: set[int],
    queue_getter: Callable[[], Awaitable[list]],
    stats_getter: Callable[[int], Awaitable[dict[str, int]]],
    force_generate: Callable[[], Awaitable[int]],
) -> None:
    @dp.message(Command("queue"))
    async def queue_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        queue = await queue_getter()
        if not queue:
            await message.answer("Queue is empty.")
            return
        lines = [f"#{item.id} status={item.status.value}" for item in queue]
        await message.answer("\n".join(lines))

    @dp.message(Command("stats"))
    async def stats_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        s7, s30, s90 = await stats_getter(7), await stats_getter(30), await stats_getter(90)
        await message.answer(f"7d={s7}\n30d={s30}\n90d={s90}")

    @dp.message(Command("force_generate"))
    async def force_generate_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        generated = await force_generate()
        await message.answer(f"Generated drafts: {generated}")
