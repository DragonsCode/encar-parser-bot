from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging
from database.db_session import global_init
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from database import DBApi
from tgbot.handlers import commands_router
# from functions import parse_cars
from functions.mobile import parse_full_car_info, parse_cars, parse_car_details, parse_accident_summary, init_browser
from tasks import run_parser_periodically, check_subscriptions


async def get_bot_token():
    async with DBApi() as db:
        setting = await db.get_setting_by_key("telegram_bot_token")
        if not setting or not setting.value:
            raise ValueError("Токен Telegram бота не найден в настройках базы данных")
        return setting.value


async def main(run_bot=True, run_parser=False):
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация базы данных
    await global_init(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        delete_db=False  # Установите True, если нужно пересоздать таблицы
    )
    tg_bot_token = await get_bot_token()
    bot = Bot(token=tg_bot_token)
    dp = Dispatcher()
    
    # Подключение роутеров
    dp.include_router(commands_router)

    # Запуск планировщика
    # if run_scheduler:
    #     scheduler = AsyncIOScheduler()
    #     scheduler.add_job(run_parser_periodically, 'interval', hours=48)
    #     scheduler.add_job(check_subscriptions, 'interval', hours=24)
    #     scheduler.start()
    #     logging.info("Планировщик запущен")

    # Запуск парсера
    if run_parser:
        await init_browser()
        print("Запускаю парсинг...")
        res = await parse_cars('kor', max_pages=2)
        print("Количество автомобилей: ", len(res))
        print("CARS: ", res)
        car = res[0]
        car_id = car['id']
        car['url'] = car['url'].replace('https://car.encar.com', '')
        details = await parse_car_details(car['url'])
        accident_data = await parse_accident_summary(str(car['id']))
        print(f"SELECTED CAR: {car}")
        print(f"URL: {car['url']}")
        print(f"CAR ID: {car_id}")
        print(f"DETAILS: {details}")
        print(f"ACCIDENTS: {accident_data}")
        await parse_full_car_info('kor', max_pages=1)

    if run_bot:
        # Запуск бота
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main(run_bot=True, run_parser=False))