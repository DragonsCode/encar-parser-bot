import asyncio
from os import getenv
from openai import AsyncOpenAI
import openai
from database import DBApi
from database.manufacture import Manufacture
from database.models import Models
from database.series import Series
from database.equipment import Equipment
from database.engine_type import EngineType
from database.drive_type import DriveType
from database.car_color import CarColor
from sqlalchemy import select
from dotenv import load_dotenv
import json
import re
from openai import AsyncOpenAI

load_dotenv()

# Initialize OpenAI client for DeepSeek API
deepseek_api_key = getenv("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    raise ValueError("DeepSeek API key not found. Set the DEEPSEEK_API_KEY environment variable.")

client = AsyncOpenAI(
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com/v1"
)

async def translate_text(text: str, context: str) -> str:
    """
    Переводит текст с корейского на английский через DeepSeek API, возвращая только переведённый текст.
    
    Args:
        text: Текст для перевода (на корейском).
        context: Контекст перевода (не используется, оставлен для совместимости).
    
    Returns:
        Переведённый текст на английском или исходный текст при ошибке.
    """
    try:
        # Нормализация входного текста
        normalized_text = ' '.join(text.strip().split())
        if not normalized_text:
            return text.capitalize()
        
        # Запрос перевода через DeepSeek API
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Вы переводчик. Переведите данный корейский текст на английский и верните только переведённый текст в формате JSON с ключом 'translated_text'. Не добавляйте пояснений или лишнего текста."},
                {"role": "user", "content": normalized_text}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        # Извлечение содержимого ответа
        response_text = response.choices[0].message.content.strip()
        
        # Извлечение JSON из блоков кода, если они есть
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_content = json_match.group(1)
        else:
            json_content = response_text
        
        # Парсинг JSON и извлечение перевода
        try:
            translation_data = json.loads(json_content)
            translated_text = translation_data.get('translated_text', text)
        except json.JSONDecodeError:
            print(f"Ошибка парсинга JSON из ответа: {response_text}")
            translated_text = text
        
        # Нормализация и приведение к правильному регистру
        normalized_translated = ' '.join(translated_text.strip().split())
        return normalized_translated.capitalize() if normalized_translated else text.capitalize()
    except Exception as e:
        print(f"Ошибка перевода текста '{text}' (контекст: {context}): {e}")
        return text.capitalize()

async def translate_table_data():
    """Переводит данные в таблицах с корейского на английский с помощью GPT-4o-mini."""
    tables = [
        # (Manufacture, "manufacture"),
        # (Models, "models"),
        (Series, "series"),
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