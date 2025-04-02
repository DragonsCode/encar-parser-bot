from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from aiogram import Bot
from database import DBApi
from database.db_session import global_init
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from tgbot.keyboards.inline import get_more_cars_keyboard

async def get_bot():
    async with DBApi() as db:
        setting = await db.get_setting_by_key("telegram_bot_token")
        if not setting or not setting.value:
            raise ValueError("Токен Telegram бота не найден")
        return Bot(token=setting.value)

async def check_new_cars():
    print("Проверка новых автомобилей...")
    async with DBApi() as db:
        filters = await db.get_all_filters()
        bot = await get_bot()
        try:
            for filter_obj in filters:
                user_id = filter_obj.user_id
                filter_id = filter_obj.id

                new_cars = await db.get_new_cars_by_filter(filter_id, user_id, limit=1)
                if new_cars:
                    car = new_cars[0]
                    message_text = (
                        f"Новый автомобиль по вашему фильтру: {car.id}\n"
                        f"Цена: {car.price_rub} руб.\n"
                        f"Пробег: {car.mileage} км\n"
                        f"Ссылка: {car.url}"
                    )

                    keyboard = get_more_cars_keyboard(filter_id)

                    await bot.send_message(user_id, message_text, reply_markup=keyboard)
                    await db.create_viewed_car(user_id, filter_id, car.id)
        finally:
            await bot.session.close()
    print("Проверка завершена.")

async def run_scheduler():
    await global_init(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        delete_db=False
    )
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_new_cars, 'interval', days=1)
    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Планировщик остановлен")

if __name__ == "__main__":
    asyncio.run(run_scheduler())