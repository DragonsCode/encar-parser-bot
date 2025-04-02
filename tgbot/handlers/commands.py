from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, CommandObject
import asyncio
from tgbot.keyboards.inline import get_web_app_keyboard, get_more_cars_keyboard
from functions import parse_cars
from database import DBApi

commands_router = Router()

@commands_router.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject):
    async with DBApi() as db:
        user = await db.create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        web_app_url = await db.get_setting_by_key("web_app_url")
    kb = get_web_app_keyboard(web_app_url.value)
    await message.answer("Привет! Я бот для поиска авто на Encar.com.\nОткрой приложение!", reply_markup=kb)

@commands_router.message(Command("help"))
async def command_help_handler(message: Message, command: CommandObject):
    await message.answer(f"Привет, {message.from_user.full_name}!\nЯ бот для поиска авто на Encar.com! Нажми на /start")

# @commands_router.message(Command("search"))
async def command_search_handler(message: Message, command: CommandObject):
    result = await parse_cars(command.args)
    for car in result:
        text = f"ID: {car['id']}\nНазвание: {car['name']}\nЦена: {car['price_won']} Won\nСсылка: {car['url']}\n\nПроизводитель: {car['manufacture']}\nМодель: {car['model']}\nСерия: {car['series']}"
        await message.answer(text)
        await asyncio.sleep(0.5)


@commands_router.callback_query(F.data.startswith("more_cars:"))
async def more_cars_handler(callback_query: CallbackQuery, bot: Bot):
    filter_id = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    async with DBApi() as db:
        filter_obj = await db.get_filter_by_id(filter_id)
        if not filter_obj:
            await bot.send_message(user_id, "Фильтр не найден.")
            return

        cars = await db.get_unviewed_cars_by_filter(filter_id, user_id, limit=1)
        if not cars:
            await bot.send_message(user_id, "Все автомобили просмотрены.")
            return

        car = cars[0]
        message_text = (
            f"Автомобиль: {car.id}\n"
            f"Цена: {car.price_rub} руб.\n"
            f"Пробег: {car.mileage} км\n"
            f"Ссылка: {car.url}"
        )

        keyboard = get_more_cars_keyboard(filter_id)

        await bot.send_message(user_id, message_text, reply_markup=keyboard)
        await db.create_viewed_car(user_id, filter_id, car.id)