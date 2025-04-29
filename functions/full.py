import asyncio
import aiohttp
from datetime import datetime
from database import DBApi
from os import getenv
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

async def translate_text(text: str, context: str) -> str:
    """
    Переводит текст с корейского на английский с помощью GoogleTranslator.
    
    Args:
        text: Текст для перевода (на корейском).
        context: Контекст перевода (не используется в GoogleTranslator, оставлен для совместимости).
    
    Returns:
        Переведённый текст на английском или оригинальный текст при ошибке.
    """
    try:
        translator = GoogleTranslator(source='ko', target='en')
        translated_text = translator.translate(text)
        return translated_text.capitalize() if translated_text else text.capitalize()
    except Exception as e:
        print(f"Ошибка перевода текста '{text}' (контекст: {context}): {e}")
        return text.capitalize()

async def get_exchange_rate():
    """Получает текущий курс обмена KRW к RUB."""
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.exchangerate-api.com/v4/latest/KRW') as response:
            if response.status == 200:
                data = await response.json()
                return data['rates']['RUB']
            else:
                print(f"Ошибка получения курса обмена: {response.status}")
                return None

async def fetch_api_data(url: str, params: dict = None):
    """Получает данные из API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Ошибка при запросе {url}: {response.status}")
                return None

async def parse_cars(car_type: str, max_pages: int = None):
    """Генератор, возвращающий автомобили постранично из API."""
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
            "inav": "|Metadata|Sort"
        }
        
        data = await fetch_api_data(base_url, params)
        if not data or 'SearchResults' not in data or not data['SearchResults']:
            print(f"Страница {page_num} не содержит автомобилей, завершаем парсинг {car_type}.")
            break
        
        total_count = data.get('Count', 0)
        print(f"Страница {page_num}: найдено {len(data['SearchResults'])} автомобилей, всего доступно {total_count}")
        
        yield data['SearchResults']
        
        offset += page_size
        page_num += 1
        await asyncio.sleep(1)

async def parse_car_details(car_id: str):
    """Получает детальную информацию об автомобиле из API."""
    url = f"https://api.encar.com/v1/readside/vehicle/{car_id}"
    params = {"include": "ADVERTISEMENT,CATEGORY,CONDITION,CONTACT,MANAGE,OPTIONS,PHOTOS,SPEC,PARTNERSHIP,CENTER,VIEW"}
    return await fetch_api_data(url, params)

async def parse_accident_summary(car_id: str, vehicle_no: str):
    """Получает информацию о страховой истории автомобиля из API."""
    url = f"https://api.encar.com/v1/readside/record/vehicle/{car_id}/open"
    params = {"vehicleNo": vehicle_no}
    return await fetch_api_data(url, params)

async def normalize_text(text: str) -> str:
    """Нормализует текст: удаляет лишние пробелы и переводит в нижний регистр для сравнения."""
    return ' '.join(text.strip().lower().split())

async def process_entity(db: DBApi, entity_type: str, name: str, parent_id: int = None, parent_field: str = None):
    """
    Обрабатывает сущность: ищет по имени, если не найдено — переводит и проверяет по имени и переводу.
    
    Args:
        db: Экземпляр DBApi.
        entity_type: Тип сущности ('manufacture', 'model', 'series', 'equipment', 'engine_type', 'drive_type', 'car_color').
        name: Оригинальное имя.
        parent_id: ID родительской сущности (для моделей, серий, комплектаций).
        parent_field: Поле родительской сущности (например, 'manufacture_id' для моделей).
    
    Returns:
        Объект сущности.
    """
    normalized_name = await normalize_text(name)
    
    # Сначала ищем по имени
    if entity_type == 'manufacture':
        entity = await db.get_manufacture_by_name(normalized_name)
    elif entity_type == 'model':
        entity = await db.get_model_by_name(normalized_name)
    elif entity_type == 'series':
        entity = await db.get_series_by_name(normalized_name)
    elif entity_type == 'equipment':
        entity = await db.get_equipment_by_name(normalized_name)
    elif entity_type == 'engine_type':
        entity = await db.get_engine_type_by_name(normalized_name)
    elif entity_type == 'drive_type':
        entity = await db.get_drive_type_by_name(normalized_name)
    elif entity_type == 'car_color':
        entity = await db.get_car_color_by_name(normalized_name)
    else:
        raise ValueError(f"Неизвестный тип сущности: {entity_type}")
    
    if entity:
        return entity
    
    # Если не найдено, переводим
    translated = await translate_text(name, entity_type)
    normalized_translated = await normalize_text(translated)
    
    # Проверяем по имени и переводу
    if entity_type == 'manufacture':
        entity = await db.get_manufacture_by_name_and_translated(normalized_name, normalized_translated)
    elif entity_type == 'model':
        entity = await db.get_model_by_name_and_translated(normalized_name, normalized_translated, parent_id)
    elif entity_type == 'series':
        entity = await db.get_series_by_name_and_translated(normalized_name, normalized_translated, parent_id)
    elif entity_type == 'equipment':
        entity = await db.get_equipment_by_name_and_translated(normalized_name, normalized_translated, parent_id)
    elif entity_type == 'engine_type':
        entity = await db.get_engine_type_by_name_and_translated(normalized_name, normalized_translated)
    elif entity_type == 'drive_type':
        entity = await db.get_drive_type_by_name_and_translated(normalized_name, normalized_translated)
    elif entity_type == 'car_color':
        entity = await db.get_car_color_by_name_and_translated(normalized_name, normalized_translated)
    
    if entity:
        return entity
    
    # Если не найдено, создаем новую запись
    if entity_type == 'manufacture':
        entity = await db.create_manufacture(name=normalized_name, translated=normalized_translated)
    elif entity_type == 'model':
        entity = await db.create_model(manufacture_id=parent_id, name=normalized_name, translated=normalized_translated)
    elif entity_type == 'series':
        entity = await db.create_series(models_id=parent_id, name=normalized_name, translated=normalized_translated)
    elif entity_type == 'equipment':
        entity = await db.create_equipment(series_id=parent_id, name=normalized_name, translated=normalized_translated)
    elif entity_type == 'engine_type':
        entity = await db.create_engine_type(name=normalized_name, translated=normalized_translated)
    elif entity_type == 'drive_type':
        entity = await db.create_drive_type(name=normalized_name, translated=normalized_translated)
    elif entity_type == 'car_color':
        entity = await db.create_car_color(name=normalized_name, translated=normalized_translated)
    
    return entity

async def fetch_car_full_info(car, exchange_rate, sem: asyncio.Semaphore):
    """Обрабатывает полную информацию об автомобиле и записывает в БД."""
    async with sem:
        try:
            print(f"Начало обработки автомобиля {car['Id']}")
            details = await parse_car_details(car['Id'])
            if not details or 'vehicleNo' not in details:
                print(f"Не удалось получить детали для автомобиля {car['Id']}")
                return
            
            accident_data = await parse_accident_summary(car['Id'], details['vehicleNo'])
            if not accident_data:
                print(f"Не удалось получить историю аварий для автомобиля {car['Id']}")
                return

            manufacture_name_original = car.get('Manufacturer', details.get('category', {}).get('manufacturerName', 'Unknown'))
            model_name_original = car.get('ModelGroup', details.get('category', {}).get('modelName', 'Unknown'))
            series_name_original = car.get('Model', details.get('category', {}).get('gradeName', 'Unknown'))
            
            async with DBApi() as db:
                # Обработка производителя
                manufacture = await process_entity(db, 'manufacture', manufacture_name_original)
                car['manufacture_id'] = manufacture.id
                
                # Обработка модели
                model = await process_entity(db, 'model', model_name_original, parent_id=car['manufacture_id'], parent_field='manufacture_id')
                car['model_id'] = model.id
                
                # Обработка серии
                series = await process_entity(db, 'series', series_name_original, parent_id=car['model_id'], parent_field='models_id')
                car['series_id'] = series.id
                
                # Обработка комплектации
                equipment_original = car.get('Badge')
                if equipment_original:
                    equipment = await process_entity(db, 'equipment', equipment_original, parent_id=car['series_id'], parent_field='series_id')
                    car['equipment_id'] = equipment.id
                else:
                    car['equipment_id'] = None
                
                # Обработка типа двигателя
                engine_type_original = car.get('FuelType', details.get('spec', {}).get('fuelName'))
                if engine_type_original:
                    engine_type = await process_entity(db, 'engine_type', engine_type_original)
                    car['engine_type_id'] = engine_type.id
                else:
                    car['engine_type_id'] = None
                
                # Обработка типа привода
                drive_type_original = car.get('Transmission')
                if drive_type_original:
                    drive_type = await process_entity(db, 'drive_type', drive_type_original)
                    car['drive_type_id'] = drive_type.id
                else:
                    car['drive_type_id'] = None
                
                # Обработка цвета автомобиля
                car_color_original = car.get('Color', details.get('spec', {}).get('colorName'))
                if car_color_original:
                    car_color = await process_entity(db, 'car_color', car_color_original)
                    car['car_color_id'] = car_color.id
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
                
                print(f"Сохранение автомобиля {car['Id']} в базу данных")
                await db.create_car(**car_data)
                print(f"Добавлен автомобиль с id={car['Id']}")
        except Exception as e:
            print(f"Ошибка при обработке автомобиля {car['Id']}: {e}")

async def parse_full_car_info(max_pages: int = None):
    """Основная функция для парсинга полной информации об автомобилях."""
    exchange_rate = await get_exchange_rate()
    if not exchange_rate:
        print("Не удалось получить курс обмена, завершение работы.")
        return
    
    for car_type in ['kor', 'ev']:
        print(f"Парсинг автомобилей типа '{car_type}'...")
        async for page_cars in parse_cars(car_type, max_pages):
            async with DBApi() as db_temp:
                existing_ids = set(await db_temp.get_all_car_ids())
            new_cars = [car for car in page_cars if car['Id'] not in existing_ids]
            print(f"Найдено новых автомобилей на странице: {len(new_cars)} из {len(page_cars)}")
            
            sem = asyncio.Semaphore(5)
            tasks = [fetch_car_full_info(car, exchange_rate, sem) for car in new_cars]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            del page_cars
            del new_cars
            await asyncio.sleep(1)
    
    print("Парсинг завершен.")

if __name__ == "__main__":
    asyncio.run(parse_full_car_info())