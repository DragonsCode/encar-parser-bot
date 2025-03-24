from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from database import DBApi
from database.db_session import global_init
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from tgbot.keyboards.inline import get_web_app_keyboard


async def get_bot():
    """Инициализирует Telegram-бота с токеном из базы данных."""
    async with DBApi() as db:
        setting = await db.get_setting_by_key("telegram_bot_token")
        if not setting or not setting.value:
            raise ValueError("Токен Telegram бота не найден в настройках базы данных")
        return Bot(token=setting.value)

async def check_subscriptions():
    """Проверяет подписки и отправляет уведомления об истечении."""
    print("Проверка подписок на истечение...")
    now = datetime.now()
    expiration_threshold = now + timedelta(hours=24)
    
    async with DBApi() as db:
        expiring_subscriptions = await db.get_expiring_subscriptions(now, expiration_threshold)
        
        if not expiring_subscriptions:
            print("Нет подписок, истекающих в ближайшие 24 часа.")
            return
        
        bot = await get_bot()
        web_app_url = await db.get_setting_by_key("web_app_url")
        kb = get_web_app_keyboard(web_app_url.value)
        try:
            for sub in expiring_subscriptions:
                time_left = sub.subscription_end - now
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                
                message = (
                    f"Ваша подписка истекает через {hours_left} часов и {minutes_left} минут!\n"
                    f"Дата окончания: {sub.subscription_end.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    "Пожалуйста, продлите подписку, чтобы продолжить использование сервиса."
                )
                
                try:
                    await bot.send_message(chat_id=sub.user_id, text=message, reply_markup=kb)
                    print(f"Отправлено уведомление пользователю {sub.user_id}")
                    await asyncio.sleep(0.4)
                except Exception as e:
                    print(f"Ошибка отправки уведомления пользователю {sub.user_id}: {e}")
        finally:
            await bot.session.close()
    
    print("Проверка подписок завершена.")

async def check_and_remove_filters():
    """Проверяет подписки и удаляет лишние фильтры пользователей."""
    print("Проверка фильтров пользователей...")
    async with DBApi() as db:
        users = await db.get_all_users()
        for user in users:
            user_id = user.id
            active_sub = await db.get_active_subscription_by_user(user_id)
            filters = await db.get_filters_by_user(user_id)
            filters_count = len(filters)

            if not active_sub:
                for filter_obj in filters:
                    await db.delete_filter(filter_obj.id)
                print(f"Удалены все фильтры пользователя {user_id}")
            else:
                tariff = await db.get_tariff_by_id(active_sub.tariff_id)
                if tariff:
                    allowed_filters = tariff.filters_count
                    if filters_count > allowed_filters:
                        filters_to_delete = filters[:filters_count - allowed_filters]
                        for filter_obj in filters_to_delete:
                            await db.delete_filter(filter_obj.id)
                        print(f"Удалены {len(filters_to_delete)} лишних фильтров пользователя {user_id}")
                else:
                    print(f"Тариф с id={active_sub.tariff_id} не найден для пользователя {user_id}")

    print("Проверка фильтров завершена.")

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
    scheduler.add_job(check_subscriptions, 'interval', hours=24)
    scheduler.add_job(check_and_remove_filters, 'interval', days=1)
    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Планировщик остановлен")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scheduler())