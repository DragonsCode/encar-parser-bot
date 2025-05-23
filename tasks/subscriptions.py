from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from database import DBApi
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
    expiration_threshold = now + timedelta(hours=24)  # Порог истечения: следующие 24 часа
    
    async with DBApi() as db:
        # Используем новый метод для получения подписок
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
            await bot.session.close()  # Закрываем сессию бота
    
    print("Проверка подписок завершена.")

# Для тестирования вручную
if __name__ == "__main__":
    # asyncio.run(check_subscriptions())
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_subscriptions, 'interval', hours=48)
    scheduler.start()