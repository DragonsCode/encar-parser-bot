from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, CommandObject
import aiogram.utils.markdown as fmt
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
        
        count_db = await db.get_setting_by_key("sent_cars_count")
        count = count_db.value if count_db else 0
        for car in cars:
            if count <= 0:
                break
            model = await db.get_model_by_id(car.model_id)
            engine = await db.get_engine_type_by_id(car.engine_type_id)
            manufacture = await db.get_manufacture_by_id(car.manufacture_id)
            series = await db.get_series_by_id(car.series_id)
            update_date = car.update_dttm.strftime("%Y-%m-%d %H:%M")
            date_release = car.date_release.strftime("%Y-%m")
            
            car_data = {
                "id": car.id,
                "manufacture": manufacture.translated,
                "model": model.translated,
                "series": series.translated,
                "mileage": car.mileage,
                "year": date_release,
                "engine": engine.translated,
                "price_won": car.price_won,
                "price_rub": car.price_rub,
                "update_date": update_date,
                "check_date": car.check_dttm,
                "owner_changes": car.change_ownership,
                "total_accidents": car.all_traffic_accident,
                "owner_fault_accidents": car.traffic_accident_owner,
                "other_fault_accidents": car.traffic_accident_other,
                "owner_repair_cost": car.repair_cost_owner,
                "other_repair_cost": car.repair_cost_other,
                "theft": car.theft,
                "flood": car.flood,
                "total_loss": car.death,
                "link": car.url
            }
            message_text = (
                f"🆔: {car_data.get('id', 'N/A')}\n"
                f"🚗 {car_data.get('manufacture', '')} {car_data.get('model', '')} {car_data.get('series', '')}\n"
                f"📆 Дата обновления: {car_data.get('update_date', 'N/A')}\n"
                f"📈 Пробег: {car_data.get('mileage', 'N/A')} км\n"
                f"🗓 Год: {car_data.get('year', 'N/A')}\n"
                f"🔥 Тип двигателя: {car_data.get('engine', 'N/A')}\n"
                f"💵 Цена (won): {car_data.get('price_won', 'N/A'):,}\n"
                f"💵 Цена (руб): ~{car_data.get('price_rub', 'N/A'):,}\n"
                "---\n"
                f"📝 Страховая история:\n"
                f"📆 Дата проверки: {car_data.get('check_date', 'N/A')}\n"
                f"🙎‍ Смена владельцев: {car_data.get('owner_changes', 0)}\n"
                f"🚨 Общее кол-во ДТП: {car_data.get('total_accidents', 0)}\n"
                f"🚨 ДТП по вине владельца: {car_data.get('owner_fault_accidents', 0)}\n"
                f"🚨 ДТП по вине других: {car_data.get('other_fault_accidents', 0)}\n"
                f"💵 Расходы на ремонт (виновник - владелец): {car_data.get('owner_repair_cost', 0)} won\n"
                f"💵 Расходы на ремонт (виновник - другое авто): {car_data.get('other_repair_cost', 0)} won\n"
                f"🥷🏻 Угон: {car_data.get('theft', 0)}\n"
                f"🌊 Наводнения: {car_data.get('flood', 0)}\n"
                f"🧨 Кол-во (полная гибель): {car_data.get('total_loss', 0)}\n"
                "🌐 Страница на " + fmt.hlink("Encar.com", car_data.get('link', 'https://encar.com/'))
            )

            keyboard = get_more_cars_keyboard(filter_id)
            if count == 1:
                await bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await bot.send_message(user_id, message_text, parse_mode="HTML")
            await db.create_viewed_car(user_id, filter_id, car.id)
            count -= 1