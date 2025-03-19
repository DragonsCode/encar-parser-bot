from deep_translator import GoogleTranslator
from database import DBApi
from database.manufacture import Manufacture
from database.models import Models
from database.series import Series
from database.equipment import Equipment
from database.engine_type import EngineType
from database.drive_type import DriveType
from database.car_color import CarColor
from sqlalchemy import select
import asyncio

async def translate_table_data():
    """Переводит данные в таблицах с корейского на русский."""
    translator = GoogleTranslator(source='ko', target='ru')  # ko - корейский, ru - русский
    
    # Список таблиц и их моделей
    tables = [
        (Manufacture, "manufacture"),
        (Models, "models"),
        (Series, "series"),
        (Equipment, "equipment"),
        (EngineType, "engine_type"),
        (DriveType, "drive_type"),
        (CarColor, "car_color")
    ]
    
    async with DBApi() as db:
        for model, table_name in tables:
            print(f"Перевод таблицы: {table_name}")
            # Получаем все записи из таблицы
            result = await db._sess.execute(select(model))
            records = result.scalars().all()
            
            for record in records:
                if record.name and not record.name.isascii():  # Проверяем, что текст на корейском
                    try:
                        translated_name = translator.translate(record.name)
                        print(f"Переведено: {translated_name} (было: {record.name})")
                        record.name = translated_name
                    except Exception as e:
                        print(f"Ошибка перевода для {record.name}: {e}")
                        continue
            
            # Фиксируем изменения в базе
            await db._sess.commit()
            print(f"Таблица {table_name} переведена и сохранена")

async def run_translation():
    """Запускает перевод данных."""
    try:
        await translate_table_data()
    except Exception as e:
        print(f"Ошибка при запуске перевода: {e}")

if __name__ == "__main__":
    asyncio.run(run_translation())