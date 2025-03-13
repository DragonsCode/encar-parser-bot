from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command, CommandObject
from functions import parse_cars
import asyncio

commands_router = Router()

@commands_router.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject):
    await message.answer("Привет! Я бот для поиска авто на Encar.com.\nОткрой приложение: t.me/YourBotName?start=app")

@commands_router.message(Command("help"))
async def command_help_handler(message: Message, command: CommandObject):
    await message.answer(f"Привет, {message.from_user.full_name}!\n!")

@commands_router.message(Command("search"))
async def command_search_handler(message: Message, command: CommandObject):
    result = await parse_cars(command.args)
    for car in result:
        text = f"ID: {car['id']}\nНазвание: {car['name']}\nЦена: {car['price_won']} Won\nСсылка: {car['url']}\n\nПроизводитель: {car['manufacture']}\nМодель: {car['model']}\nСерия: {car['series']}"
        await message.answer(text)
        await asyncio.sleep(0.5)