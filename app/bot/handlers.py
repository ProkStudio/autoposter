from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import admin_menu_keyboard

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
    send_to_moderation: Callable[[], Awaitable[int]],
    publish_now: Callable[[], Awaitable[str]],
    overview_getter: Callable[[], Awaitable[dict[str, int]]],
) -> None:
    async def show_admin_menu(message: Message) -> None:
        await message.answer("Админ-меню готово.", reply_markup=admin_menu_keyboard())

    @dp.message(Command("start"))
    async def start_menu_cmd(message: Message) -> None:
        if message.from_user and admin_only(admin_ids, message.from_user.id):
            await show_admin_menu(message)
        else:
            await message.answer("Football autopost bot is running.")

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

    @dp.message(Command("menu"))
    async def menu_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        await show_admin_menu(message)

    @dp.message(Command("publish_now"))
    async def publish_now_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        await message.answer(await publish_now())

    @dp.message(Command("overview"))
    async def overview_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        overview = await overview_getter()
        await message.answer(
            "Сводка:\n"
            f"- Опубликовано всего: {overview['published_total']}\n"
            f"- Опубликовано за 24ч: {overview['published_24h']}\n"
            f"- Ожидают модерации: {overview['in_moderation']}\n"
            f"- Черновики: {overview['drafts']}"
        )

    @dp.message(Command("send_to_moderation"))
    async def send_to_moderation_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        sent = await send_to_moderation()
        await message.answer(f"Sent to moderation: {sent}")

    @dp.message()
    async def menu_buttons(message: Message) -> None:
        if not message.from_user or not admin_only(admin_ids, message.from_user.id):
            return
        text = (message.text or "").strip()
        if text == "📊 Сводка":
            overview = await overview_getter()
            await message.answer(
                "Сводка:\n"
                f"- Опубликовано всего: {overview['published_total']}\n"
                f"- Опубликовано за 24ч: {overview['published_24h']}\n"
                f"- Ожидают модерации: {overview['in_moderation']}\n"
                f"- Черновики: {overview['drafts']}"
            )
        elif text == "🗂 Очередь":
            queue = await queue_getter()
            if not queue:
                await message.answer("Queue is empty.")
                return
            lines = [f"#{item.id} status={item.status.value}" for item in queue]
            await message.answer("\n".join(lines))
        elif text == "⚡ Сгенерировать":
            generated = await force_generate()
            await message.answer(f"Generated drafts: {generated}")
        elif text == "🛂 В модерацию":
            sent = await send_to_moderation()
            await message.answer(f"Sent to moderation: {sent}")
        elif text == "🚀 Опубликовать сейчас":
            await message.answer(await publish_now())
        elif text == "📈 Статистика":
            s7, s30, s90 = await stats_getter(7), await stats_getter(30), await stats_getter(90)
            await message.answer(f"7d={s7}\n30d={s30}\n90d={s90}")
