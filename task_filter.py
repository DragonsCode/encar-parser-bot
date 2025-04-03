from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from aiogram import Bot
import aiogram.utils.markdown as fmt
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
                    model = await db.get_model_by_id(car.model_id)
                    engine = await db.get_engine_type_by_id(car.engine_type_id)
                    manufacture = await db.get_manufacture_by_id(car.manufacture_id)
                    series = await db.get_series_by_id(car.series_id)
                    
                    car_data = {
                        "id": car.id,
                        "manufacture": manufacture.translated,
                        "model": model.translated,
                        "series": series.translated,
                        "mileage": car.mileage,
                        "year": car.date_release,
                        "engine": engine.translated,
                        "price_won": car.price_won,
                        "price_rub": car.price_rub,
                        "update_date": car.update_dttm,
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

                    await bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode="HTML")
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