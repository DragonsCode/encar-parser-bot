import asyncio
import aiohttp
import requests
import json
import re
import pickle
import os
from datetime import datetime
from database import DBApi
from os import getenv
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Инициализация клиента OpenAI для DeepSeek API
deepseek_api_key = getenv("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    raise ValueError("DeepSeek API key not found. Set the DEEPSEEK_API_KEY environment variable.")

client = AsyncOpenAI(
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com/v1"
)

# Единый User-Agent для согласованности с браузером
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0"

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
        normalized_text = ' '.join(text.strip().split())
        if not normalized_text:
            return text.capitalize()
        
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Вы переводчик. Переведите данный корейский текст на английский и верните только переведённый текст в формате JSON с ключом 'translated_text'. Не добавляйте пояснений или лишнего текста."},
                {"role": "user", "content": normalized_text}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        response_text = response.choices[0].message.content.strip()
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        json_content = json_match.group(1) if json_match else response_text
        
        try:
            translation_data = json.loads(json_content)
            translated_text = translation_data.get('translated_text', text)
        except json.JSONDecodeError:
            print(f"Ошибка парсинга JSON из ответа: {response_text}")
            translated_text = text
        
        normalized_translated = ' '.join(translated_text.strip().split())
        return normalized_translated.capitalize() if normalized_translated else text.capitalize()
    except Exception as e:
        print(f"Ошибка перевода текста '{text}' (контекст: {context}): {e}")
        return text.capitalize()

async def load_cookies():
    """Загружает куки из файла."""
    cookie_file = "cookies/encar_cookies.dat"
    if os.path.exists(cookie_file):
        with open(cookie_file, "rb") as f:
            cookies = pickle.load(f)
        return cookies
    return None

async def fetch_api_data(url: str, params: dict = None, headers: dict = None):
    """Получает данные из API с использованием aiohttp и куки."""
    cookies = await load_cookies()
    cookies_dict = {cookie.name: cookie.value for cookie in cookies} if cookies else {}
    if not headers:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://car.encar.com/",
            "User-Agent": USER_AGENT
        }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Ошибка при запросе {url}: {response.status}")
                return None

async def get_exchange_rate():
    """Получает текущий курс обмена KRW на RUB."""
    url = 'https://api.exchangerate-api.com/v4/latest/KRW'
    data = await fetch_api_data(url)
    if data:
        return data['rates']['RUB']
    else:
        print("Не удалось получить курс обмена.")
        return None

async def parse_cars(car_type: str, max_pages: int = None):
    """Генератор, возвращающий машины постранично из API."""
    base_url = "https://api.encar.com/search/car/list/mobile"
    if car_type == 'kor':
        q = "(And.Hidden.N._.CarType.A.)"
    elif car_type == 'ev':
        q = "(And.Hidden.N._.CarType.A._.GreenType.Y.)"
    else:
        raise ValueError("Неверный car_type. Используйте 'kor' или 'ev'.")
    
    page_size = 200
    offset = 0
    page_num = 1
    
    while True:
        if max_pages and page_num > max_pages:
            break
        
        params = {
            "count": "true",
            "q": q,
            "sr": f"|MobileModifiedDate|{offset}|{page_size}",
            "inav": "|Metadata|Sort",
            "cursor": ""
        }
        url = f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr=%7CMobileModifiedDate%7C{offset}%7C{page_size}"
        
        data = await fetch_api_data(url)
        if not data or 'SearchResults' not in data or not data['SearchResults']:
            print(f"Страница {page_num} не содержит машин, завершаем парсинг {car_type}.")
            break
        
        total_count = data.get('Count', 0)
        print(f"Страница {page_num}: найдено {len(data['SearchResults'])} машин, всего доступно {total_count}")
        
        yield data['SearchResults']
        
        offset += page_size
        page_num += 1
        await asyncio.sleep(1)

async def parse_car_details(car_id: str):
    """Получает подробную информацию о машине из API."""
    url = f"https://api.encar.com/v1/readside/vehicle/{car_id}"
    params = {"include": "ADVERTISEMENT,CATEGORY,CONDITION,CONTACT,MANAGE,OPTIONS,PHOTOS,SPEC,PARTNERSHIP,CENTER,VIEW"}
    return await fetch_api_data(url, params)

async def parse_accident_summary(car_id: str, vehicle_no: str):
    """Получает историю страхования машины из API."""
    url = f"https://api.encar.com/v1/readside/record/vehicle/{car_id}/open"
    params = {"vehicleNo": vehicle_no}
    return await fetch_api_data(url, params)

async def fetch_car_full_info(car, exchange_rate, sem: asyncio.Semaphore):
    """Обрабатывает полную информацию о машине и сохраняет в базу данных."""
    async with sem:
        try:
            print(f"Обработка машины {car['Id']}")
            details = await parse_car_details(car['Id'])
            if not details or 'vehicleNo' not in details:
                print(f"Не удалось получить детали для машины {car['Id']}")
                return
            
            accident_data = await parse_accident_summary(car['Id'], details['vehicleNo'])
            if not accident_data:
                print(f"Не удалось получить историю аварий для машины {car['Id']}")
                return
            
            async with DBApi() as db:
                car_exists = await db.get_car_by_id(int(car['Id']))
                if car_exists:
                    print(f"Машина {car['Id']} уже существует, пропускаем")
                    return

            manufacture_name_original = car.get('Manufacturer', details.get('category', {}).get('manufacturerName', 'Unknown'))
            model_name_original = car.get('ModelGroup', details.get('category', {}).get('modelName', 'Unknown'))
            series_name_original = car.get('Model', details.get('category', {}).get('gradeName', 'Unknown'))
            
            manufacture_name_translated = await translate_text(manufacture_name_original, "manufacture")
            model_name_translated = await translate_text(model_name_original, "model")
            series_name_translated = await translate_text(series_name_original, "series")
            
            drive_type_original = car.get('Transmission')
            drive_type_translated = await translate_text(drive_type_original, "drive_type") if drive_type_original else None
            
            async with DBApi() as db:
                manufacture = await db.get_manufacture_by_name_and_translated(manufacture_name_original, manufacture_name_translated)
                if not manufacture:
                    manufacture = await db.create_manufacture(name=manufacture_name_original, translated=manufacture_name_translated)
                car['manufacture_id'] = manufacture.id
                
                model = await db.get_model_by_name_and_translated(model_name_original, model_name_translated, manufactures_id=car['manufacture_id'])
                if not model:
                    model = await db.create_model(manufacture_id=car['manufacture_id'], name=model_name_original, translated=model_name_translated)
                car['model_id'] = model.id
                
                series = await db.get_series_by_name_and_translated(series_name_original, series_name_translated, models_id=car['model_id'])
                if not series:
                    series = await db.create_series(models_id=car['model_id'], name=series_name_original, translated=series_name_translated)
                car['series_id'] = series.id
                
                equipment_original = car.get('Badge')
                if equipment_original:
                    equipment_translated = await translate_text(equipment_original, "equipment")
                    equip = await db.get_equipment_by_name_and_translated(equipment_original, equipment_translated, series_id=car['series_id'])
                    if not equip:
                        equip = await db.create_equipment(series_id=car['series_id'], name=equipment_original, translated=equipment_translated)
                    car['equipment_id'] = equip.id
                else:
                    car['equipment_id'] = None
                
                engine_type_original = car.get('FuelType', details.get('spec', {}).get('fuelName'))
                if engine_type_original:
                    engine_type_translated = await translate_text(engine_type_original, "engine_type")
                    eng_type = await db.get_engine_type_by_name_and_translated(engine_type_original, engine_type_translated)
                    if not eng_type:
                        eng_type = await db.create_engine_type(name=engine_type_original, translated=engine_type_translated)
                    car['engine_type_id'] = eng_type.id
                else:
                    car['engine_type_id'] = None
                
                if drive_type_original:
                    drv_type = await db.get_drive_type_by_name_and_translated(drive_type_original, drive_type_translated)
                    if not drv_type:
                        drv_type = await db.create_drive_type(name=drive_type_original, translated=drive_type_translated)
                    car['drive_type_id'] = drv_type.id
                else:
                    car['drive_type_id'] = None
                
                car_color_original = car.get('Color', details.get('spec', {}).get('colorName'))
                if car_color_original:
                    car_color_translated = await translate_text(car_color_original, "car_color")
                    color = await db.get_car_color_by_name_and_translated(car_color_original, car_color_translated)
                    if not color:
                        color = await db.create_car_color(name=car_color_original, translated=car_color_translated)
                    car['car_color_id'] = color.id
                else:
                    car['car_color_id'] = None
                
                price_won = car.get('Price') * 10000
                price_rub = int(price_won * exchange_rate) if price_won and exchange_rate else None
                
                year = car.get('Year')
                year_month = details.get('category', {}).get('yearMonth')
                date_release = None
                if year or year_month:
                    date_value = year if year else year_month
                    date_str = str(int(float(date_value)))
                    date_release = datetime.strptime(date_str, '%Y%m')
                
                publication_dttm_raw = details.get('manage', {}).get('firstAdvertisedDateTime')
                publication_dttm = None
                if publication_dttm_raw:
                    publication_dttm_str = publication_dttm_raw.split('.')[0]
                    publication_dttm = datetime.strptime(publication_dttm_str, '%Y-%m-%dT%H:%M:%S')
                
                check_dttm_raw = accident_data.get('regDate')
                check_dttm = None
                if check_dttm_raw:
                    check_dttm_str = check_dttm_raw.split('.')[0]
                    check_dttm = datetime.strptime(check_dttm_str, '%Y-%m-%dT%H:%M:%S')
                
                car_data = {
                    'id': int(car['Id']),
                    'manufacture_id': car['manufacture_id'],
                    'model_id': car['model_id'],
                    'series_id': car['series_id'],
                    'equipment_id': car['equipment_id'],
                    'engine_type_id': car['engine_type_id'],
                    'drive_type_id': car['drive_type_id'],
                    'car_color_id': car['car_color_id'],
                    'mileage': car.get('Mileage', details.get('spec', {}).get('mileage')),
                    'price_won': price_won,
                    'price_rub': price_rub,
                    'date_release': date_release,
                    'publication_dttm': publication_dttm,
                    'check_dttm': check_dttm,
                    'change_ownership': accident_data.get('ownerChangeCnt'),
                    'all_traffic_accident': accident_data.get('accidentCnt'),
                    'traffic_accident_owner': accident_data.get('myAccidentCnt'),
                    'traffic_accident_other': accident_data.get('otherAccidentCnt'),
                    'repair_cost_owner': accident_data.get('myAccidentCost'),
                    'repair_cost_other': accident_data.get('otherAccidentCost'),
                    'theft': 1 if accident_data.get('robberCnt', 0) > 0 else 0,
                    'flood': 1 if accident_data.get('floodTotalLossCnt', 0) > 0 else 0,
                    'death': 1 if accident_data.get('totalLossCnt', 0) > 0 else 0,
                    'url': f"https://fem.encar.com/cars/detail/{car['Id']}"
                }
                
                print(f"Сохранение машины {car['Id']} в базу данных")
                await db.create_car(**car_data)
                print(f"Добавлена машина с id={car['Id']}")
        except Exception as e:
            print(f"Ошибка обработки машины {car['Id']}: {e}")

async def parse_full_car_info(max_pages: int = None):
    """Основная функция для парсинга полной информации о машинах."""
    exchange_rate = await get_exchange_rate()
    if not exchange_rate:
        print("Не удалось получить курс обмена, завершение.")
        return
    
    for car_type in ['kor', 'ev']:
        print(f"Парсинг машин типа '{car_type}'...")
        async for page_cars in parse_cars(car_type, max_pages):
            async with DBApi() as db_temp:
                existing_ids = set(await db_temp.get_all_car_ids())
            new_cars = [car for car in page_cars if car['Id'] not in existing_ids]
            print(f"Найдено {len(new_cars)} новых машин из {len(page_cars)} на странице")
            
            sem = asyncio.Semaphore(20)
            tasks = [fetch_car_full_info(car, exchange_rate, sem) for car in new_cars]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            del page_cars
            del new_cars
            await asyncio.sleep(1)
    
    print("Парсинг завершён.")

if __name__ == "__main__":
    asyncio.run(parse_full_car_info())