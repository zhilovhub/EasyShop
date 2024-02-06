from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, CallbackData


lang_select_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
    ],
])
