from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


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


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Сводка"), KeyboardButton(text="🗂 Очередь")],
            [KeyboardButton(text="⚡ Сгенерировать"), KeyboardButton(text="🛂 В модерацию")],
            [KeyboardButton(text="🚀 Опубликовать сейчас"), KeyboardButton(text="📈 Статистика")],
        ],
        resize_keyboard=True,
    )
