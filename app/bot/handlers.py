from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import admin_menu_keyboard

router = Router()


def admin_only(admin_ids: set[int], user_id: int) -> bool:
    return user_id in admin_ids


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "/status - health\n"
        "/queue - moderation queue\n"
        "/drafts - preview drafts\n"
        "/draft_edit <id> <new text> - edit draft\n"
        "/draft_delete <id> - delete draft\n"
        "/stats - hit/miss for 7/30/90 days\n"
        "/force_generate - manually run generation\n"
        "/set_prompt <text> - set custom generation prompt\n"
        "/show_prompt - show current prompt"
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
    drafts_getter: Callable[[], Awaitable[list]],
    set_prompt: Callable[[str | None], Awaitable[str]],
    get_prompt: Callable[[], Awaitable[str]],
    edit_draft: Callable[[int, str], Awaitable[str]],
    delete_draft: Callable[[int], Awaitable[str]],
) -> None:
    prompt_input_users: set[int] = set()

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

    @dp.message(Command("drafts"))
    async def drafts_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        drafts = await drafts_getter()
        if not drafts:
            await message.answer("Черновиков пока нет.")
            return
        for item in drafts[:10]:
            await message.answer(
                f"#{item.id} | {item.status.value}\n\n{item.full_text}"
            )

    @dp.message(Command("draft_edit"))
    async def draft_edit_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3 or not parts[1].isdigit():
            await message.answer("Usage: /draft_edit <id> <new text>")
            return
        prediction_id = int(parts[1])
        new_text = parts[2].strip()
        if not new_text:
            await message.answer("New text cannot be empty.")
            return
        await message.answer(await edit_draft(prediction_id, new_text))

    @dp.message(Command("draft_delete"))
    async def draft_delete_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip().isdigit():
            await message.answer("Usage: /draft_delete <id>")
            return
        prediction_id = int(parts[1].strip())
        await message.answer(await delete_draft(prediction_id))

    @dp.message(Command("set_prompt"))
    async def set_prompt_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        raw = (message.text or "").strip()
        parts = raw.split(maxsplit=1)
        if len(parts) == 1:
            await message.answer(
                "Отправь: /set_prompt <текст промпта>\n"
                "или /set_prompt reset"
            )
            return
        value = parts[1].strip()
        if value.lower() == "reset":
            result = await set_prompt(None)
            await message.answer(result)
            return
        result = await set_prompt(value)
        await message.answer(result)

    @dp.message(Command("show_prompt"))
    async def show_prompt_cmd(message: Message) -> None:
        if not admin_only(admin_ids, message.from_user.id):
            await message.answer("Forbidden")
            return
        await message.answer(await get_prompt())

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
        elif text == "🧾 Черновики":
            drafts = await drafts_getter()
            if not drafts:
                await message.answer("Черновиков пока нет.")
                return
            for item in drafts[:10]:
                await message.answer(f"#{item.id} | {item.status.value}\n\n{item.full_text}")
        elif text == "📝 Промпт":
            prompt_input_users.add(message.from_user.id)
            await message.answer(
                "Пришли новый промпт для генерации.\n"
                "Отправь reset чтобы вернуть дефолт."
            )
        elif text == "✏️ Ред. черновик":
            await message.answer("Используй: /draft_edit <id> <новый текст>")
        elif text == "🗑 Удалить черновик":
            await message.answer("Используй: /draft_delete <id>")
        elif message.from_user.id in prompt_input_users:
            value = text
            prompt_input_users.discard(message.from_user.id)
            if value.lower() == "reset":
                await message.answer(await set_prompt(None))
            else:
                await message.answer(await set_prompt(value))
