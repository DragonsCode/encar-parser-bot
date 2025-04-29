import asyncio
import logging
from os import getenv
from database.db_session import global_init
from database import DBApi
from tasks.translate import run_translation
from functions.new_filter import send_car_by_filter


DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")
DB_NAME = getenv("DB_NAME")


async def main():
    # Инициализация базы данных
    await global_init(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        delete_db=False  # Установите True, если нужно пересоздать таблицы
    )

    # test
    await send_car_by_filter(user_id=235519518, filter_id=28, first=False)


if __name__ == "__main__":
    asyncio.run(main())