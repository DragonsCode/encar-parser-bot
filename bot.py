from aiogram import Bot, Dispatcher
import asyncio
import logging
from os import getenv
from database.db_session import global_init
from tgbot.handlers import commands_router
# from functions import parse_cars
from functions.mobile import parse_full_car_info, parse_cars, parse_car_details, parse_accident_summary, init_browser


TG_BOT_TOKEN = getenv("TG_BOT_TOKEN")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")
DB_NAME = getenv("DB_NAME")


async def main(run_bot=True):
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
    
    bot = Bot(token=TG_BOT_TOKEN)
    dp = Dispatcher()
    
    # Подключение роутеров
    dp.include_router(commands_router)

    # Запуск планировщика
    # scheduler.start()

    # Запуск парсера
    # await init_browser()
    # print("Запускаю парсинг...")
    # res = await parse_cars('kor', max_pages=2)
    # print("Количество автомобилей: ", len(res))
    # print("CARS: ", res)
    # car = res[0]
    # car_id = car['id']
    # car['url'] = car['url'].replace('https://car.encar.com', '')
    # details = await parse_car_details(car['url'])
    # accident_data = await parse_accident_summary(str(car['id']))
    # print(f"SELECTED CAR: {car}")
    # print(f"URL: {car['url']}")
    # print(f"CAR ID: {car_id}")
    # print(f"DETAILS: {details}")
    # print(f"ACCIDENTS: {accident_data}")
    await parse_full_car_info('kor', max_pages=1)

    if run_bot:
        # Запуск бота
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main(False))