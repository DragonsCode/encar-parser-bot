import asyncio
import logging
from os import getenv
from database.db_session import global_init
from database import DBApi
from tasks import run_translation

from tasks import check_subscriptions, run_translation


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
    await run_translation()


if __name__ == "__main__":
    asyncio.run(main())