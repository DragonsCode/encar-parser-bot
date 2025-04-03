import asyncio
from os import getenv
from openai import AsyncOpenAI
from database import DBApi
from database.manufacture import Manufacture
from database.models import Models
from database.series import Series
from database.equipment import Equipment
from database.engine_type import EngineType
from database.drive_type import DriveType
from database.car_color import CarColor
from sqlalchemy import select
import json

# Настройка клиента OpenAI
openai_api_key = getenv("OPENAI_API_KEY")
# if not openai_api_key:
#     raise ValueError("Не найден API-ключ OpenAI. Установите переменную окружения OPENAI_API_KEY.")

client = AsyncOpenAI(api_key=openai_api_key)

async def translate_text(text: str, table_name: str) -> str:
    """
    Переводит текст с корейского на русский с помощью GPT-4o-mini.
    
    Args:
        text: Текст для перевода (на корейском).
        table_name: Название таблицы, чтобы дать контекст для перевода.
    
    Returns:
        Переведённый текст на русском.
    """
    try:
        prompt = (
            f"Переведи следующий текст с корейского на русский. "
            f"Текст является названием или описанием в таблице '{table_name}', "
            f"которая содержит данные об автомобилях (например, производители, модели, серии, оборудование и т.д.). "
            f"Верни результат в формате JSON с полем 'translated_text', содержащим только переведённый текст. "
            f"Не добавляй объяснения, комментарии или дополнительные символы (например, эмодзи). "
            f"Если перевод невозможен, верни оригинальный текст в поле 'translated_text'.\n\n"
            f"Пример формата:\n"
            f'{{"translated_text": "переведённый текст"}}\n\n'
            f"Текст: {text}"
        )
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты профессиональный переводчик с корейского на русский, специализирующийся на автомобильной тематике."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content.strip()
        try:
            result = json.loads(response_text)
            translated_text = result["translated_text"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка парсинга JSON-ответа для текста '{text}': {response_text}, ошибка: {e}")
            return text
        
        return translated_text
    
    except Exception as e:
        print(f"Ошибка перевода текста '{text}' для таблицы '{table_name}': {e}")
        return text

async def translate_table_data():
    """Переводит данные в таблицах с корейского на русский с помощью GPT-4o-mini."""
    tables = [
        # (Manufacture, "manufacture"), # Done
        # (Models, "models"), # Done
        (Series, "series"),
        # (Equipment, "equipment"), # Done
        # (EngineType, "engine_type"), # Done
        # (DriveType, "drive_type"), # Done
        # (CarColor, "car_color") # Done
    ]
    
    BATCH_SIZE = 50  # Размер пачки для обновления
    
    async with DBApi() as db:
        for model, table_name in tables:
            print(f"Перевод таблицы: {table_name}")
            result = await db._sess.execute(select(model))
            records = result.scalars().all()
            
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                print(f"Обработка пачки {i // BATCH_SIZE + 1} из {len(records) // BATCH_SIZE + 1}")
                
                for record in batch:
                    # Проверяем, что name не пустое, текст на корейском
                    if record.name and not record.name.isascii():
                        try:
                            translated_name = await translate_text(record.name, table_name)
                            print(f"Переведено: {translated_name} (было: {record.name})")
                            record.translated = translated_name  # Записываем перевод в поле translated
                        except Exception as e:
                            print(f"Ошибка перевода для {record.name} в таблице {table_name}: {e}")
                            continue
                
                await db._sess.commit()
                print(f"Пачка {i // BATCH_SIZE + 1} сохранена")
            
            print(f"Таблица {table_name} полностью переведена и сохранена")

async def run_translation():
    """Запускает перевод данных."""
    try:
        await translate_table_data()
    except Exception as e:
        print(f"Ошибка при запуске перевода: {e}")

if __name__ == "__main__":
    asyncio.run(run_translation())