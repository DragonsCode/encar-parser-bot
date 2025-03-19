from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging
from functions import parse_full_car_info  # Импортируем основную функцию
from database.db_session import global_init
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

async def run_parser_periodically():
    """Запускает парсинг автомобилей с заданными параметрами."""
    print("Запуск периодического парсинга...")
    await parse_full_car_info(max_pages=1)  # Можно настроить max_pages
    print("Периодический парсинг завершен.")

async def run_scheduler():
    # Инициализация базы данных
    await global_init(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        delete_db=False  # Установите True, если нужно пересоздать таблицы
    )
    # run_parser_periodically()  # Вызовите функцию для проверки парсера
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_parser_periodically, 'interval', hours=48)
    scheduler.start()

    # Держим событийный цикл активным
    try:
        await asyncio.Event().wait()  # Бесконечное ожидание
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Планировщик остановлен")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scheduler())