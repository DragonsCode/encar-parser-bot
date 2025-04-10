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
if not openai_api_key:
    raise ValueError("Не найден API-ключ OpenAI. Установите переменную окружения OPENAI_API_KEY.")

client = AsyncOpenAI(api_key=openai_api_key, base_url="https://api.x.ai/v1")

async def translate_text(text: str, table_name: str) -> str:
    """
    Переводит текст с корейского на английский с помощью GPT-4o-mini.
    
    Args:
        text: Текст для перевода (на корейском).
        table_name: Название таблицы, чтобы дать контекст для перевода.
    
    Returns:
        Переведённый текст на английском.
    """
    prompt = (
        f"Translate the following text from Korean to English. "
        f"The text is a name or description in the '{table_name}' table, "
        f"which contains car-related data (e.g., manufacturers, models, series, equipment, etc.). "
        f"Return the result in JSON format with a 'translated_text' field containing only the translated text. "
        f"Do not include explanations, comments, or extra characters (e.g., emojis).\n\n"
        f"Example format:\n"
        f'{{"translated_text": "translated text"}}\n\n'
        f"Text: {text}"
    )
    
    try:
        response = await client.chat.completions.create(
            model="grok-2",
            messages=[
                {"role": "system", "content": "You are a professional translator from Korean to English, specializing in automotive terminology."},
                {"role": "user", "content": prompt}
            ],
            reasoning_effort="low",
            max_tokens=100,
            temperature=0.3
        )
        response_text = response.choices[0].message.content.strip()
        result = json.loads(response_text)
        translated_text = result["translated_text"]
        return translated_text
    
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Ошибка парсинга JSON-ответа для текста '{text}' (таблица: {table_name}): {response_text}, ошибка: {e}")
        raise  # Повторяем запрос или обрабатываем ошибку выше
    except Exception as e:
        print(f"Ошибка перевода текста '{text}' (таблица: {table_name}): {e}")
        raise

async def translate_table_data():
    """Переводит данные в таблицах с корейского на английский с помощью GPT-4o-mini."""
    tables = [
        (Manufacture, "manufacture"),
        # (Models, "models"),
        # (Series, "series"),
        # (Equipment, "equipment"),
        # (EngineType, "engine_type"),
        # (DriveType, "drive_type"),
        # (CarColor, "car_color")
    ]
    
    BATCH_SIZE = 50  # Размер пачки для обновления
    
    async with DBApi() as db:
        for model, table_name in tables:
            print(f"Перевод таблицы: {table_name}")
            result = await db._sess.execute(select(model))
            records = result.scalars().all()
            
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                print(f"Обработка пачки {i // BATCH_SIZE + 1} из {(len(records) + BATCH_SIZE - 1) // BATCH_SIZE}")
                
                for record in batch:
                    # Проверяем, что name не пустое и требует перевода
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