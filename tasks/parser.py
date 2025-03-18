from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from functions import parse_full_car_info  # Импортируем основную функцию

async def run_parser_periodically():
    """Запускает парсинг автомобилей с заданными параметрами."""
    print("Запуск периодического парсинга...")
    await parse_full_car_info(max_pages=1)  # Можно настроить max_pages
    print("Периодический парсинг завершен.")


if __name__ == "__main__":
    # asyncio.run(run_parser_periodically())
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_parser_periodically, 'interval', hours=48)
    scheduler.start()