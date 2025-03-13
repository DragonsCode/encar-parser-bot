from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup

def get_question_options_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="А")
    builder.button(text="Б")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)