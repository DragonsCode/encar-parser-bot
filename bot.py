from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
import asyncio
from functions import parse_cars
from os import getenv

# Замени на свой токен от @BotFather
BOT_TOKEN = getenv("TG_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временное хранилище фильтров (telegram_id: {фильтры})
user_filters = {235519518: {"brand": "기"}}

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    # Пока фильтры захардкодим, потом добавим настройку
    user_filters[user_id] = {"brand": "기"}  # Пример
    await message.answer(
        "Привет! Я бот для поиска авто на Encar.com.\n"
        "Открой приложение: t.me/YourBotName?start=app"
    )

async def notify_user(user_id, car):
    # Проверяем фильтры
    if user_filters.get(user_id, {}).get("brand") in car["name"]:
        text = (
            f"📷 [Фото скоро будет]\n"
            f"🆔: {car['carid']}\n"
            f"🚗 {car['name']}\n"
            f"💵 Цена: {car['price']} won"
        )
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🌐 Ссылка", url=car["link"])]
        ])
        await bot.send_message(user_id, text, reply_markup=keyboard)

async def main():
    # Запускаем парсер и отправляем данные
    cars = await parse_cars()
    for user_id in user_filters:
        for car in cars:
            await notify_user(user_id, car)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())