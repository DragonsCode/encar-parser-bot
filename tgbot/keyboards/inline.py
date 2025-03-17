from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, WebAppInfo

def get_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='+', callback_data='plus')
    builder.button(text='-', callback_data='minus')
    builder.adjust(2)
    return builder.as_markup()

def get_link_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Открыть ссылку', url=url)
    builder.adjust(1)
    return builder.as_markup()

def get_web_app_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Открыть приложение', web_app=WebAppInfo(url=url))
    builder.adjust(1)
    return builder.as_markup()