from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import Dispatcher, F, Router
from aiogram.types import CallbackQuery

router = Router()


def register_callbacks(
    dp: Dispatcher,
    approve_publish: Callable[[int], Awaitable[bool]],
    reject_prediction: Callable[[int], Awaitable[bool]],
    admin_ids: set[int],
) -> None:
    @dp.callback_query(F.data.startswith("approve:"))
    async def approve_callback(callback: CallbackQuery) -> None:
        if callback.from_user.id not in admin_ids:
            await callback.answer("Forbidden", show_alert=True)
            return
        prediction_id = int(callback.data.split(":")[1])
        approved = await approve_publish(prediction_id)
        if approved:
            await callback.answer("Approved and published")
        else:
            await callback.answer("Already processed", show_alert=True)

    @dp.callback_query(F.data.startswith("reject:"))
    async def reject_callback(callback: CallbackQuery) -> None:
        if callback.from_user.id not in admin_ids:
            await callback.answer("Forbidden", show_alert=True)
            return
        prediction_id = int(callback.data.split(":")[1])
        rejected = await reject_prediction(prediction_id)
        if rejected:
            await callback.answer("Rejected")
        else:
            await callback.answer("Already processed", show_alert=True)

    @dp.callback_query(F.data.startswith("edit:"))
    async def edit_callback(callback: CallbackQuery) -> None:
        if callback.from_user.id not in admin_ids:
            await callback.answer("Forbidden", show_alert=True)
            return
        await callback.answer("Edit flow TODO", show_alert=True)
