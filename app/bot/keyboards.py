from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def moderation_keyboard(prediction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Редактировать", callback_data=f"edit:{prediction_id}"
                ),
                InlineKeyboardButton(text="Одобрить", callback_data=f"approve:{prediction_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"reject:{prediction_id}"),
            ]
        ]
    )
