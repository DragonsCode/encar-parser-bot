from aiogram import Bot
from database import DBApi
from tgbot.keyboards.inline import get_more_cars_keyboard


async def get_bot():
    """Инициализирует Telegram-бота с токеном из базы данных."""
    async with DBApi() as db:
        setting = await db.get_setting_by_key("telegram_bot_token")
        if not setting or not setting.value:
            raise ValueError("Токен Telegram бота не найден в настройках базы данных")
        return Bot(token=setting.value)

async def send_car_by_filter(user_id: int, filter_id: int):
    bot = await get_bot()
    async with DBApi() as db:
        cars = await db.get_unviewed_cars_by_filter(filter_id, user_id, limit=1)
        if not cars:
            await bot.send_message(user_id, "Все автомобили просмотрены.")
            return

        car = cars[0]
        message_text = (
            f"Автомобиль: {car.id}\n"
            f"Цена: {car.price_rub} руб.\n"
            f"Пробег: {car.mileage} км\n"
            f"Ссылка: {car.url}"
        )

        keyboard = get_more_cars_keyboard(filter_id)

        await bot.send_message(user_id, message_text, reply_markup=keyboard)
        await db.create_viewed_car(user_id, filter_id, car.id)