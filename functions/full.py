import zendriver as zd
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from datetime import datetime
from twocaptcha import TwoCaptcha
from database import DBApi

# Ваш API-ключ от RuCaptcha
RUCAPTCHA_API_KEY = '5568f74281346b5ec0124237ff51da51'  # Замените на реальный ключ

# Функция для получения курса валют (KRW -> RUB)
async def get_exchange_rate():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.exchangerate-api.com/v4/latest/KRW') as response:
            data = await response.json()
            return data['rates']['RUB']  # Курс KRW к RUB

# Основная функция для получения HTML с обработкой капчи
async def get_html_content(url: str):
    """
    Открывает браузер, получает HTML-контент страницы.
    Если есть капча, решает её через RuCaptcha и перенаправляет на исходный URL.
    
    Аргументы:
        url (str): URL страницы для парсинга.
    
    Возвращает:
        str: HTML-контент страницы или None при ошибке.
    """
    browser = await zd.start(headless=True)
    page = await browser.get(url)
    await asyncio.sleep(10)
    html = await page.get_content()
    
    if "recaptcha" in html.lower():
        print("Обнаружена reCAPTCHA v2, решаем капчу...")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем тег <script> с grecaptcha.render для получения sitekey
        script_tag = soup.find('script', string=lambda text: text and 'grecaptcha.render' in text)
        if script_tag:
            script_text = script_tag.string
            sitekey_start = script_text.find("'sitekey' : '") + len("'sitekey' : '")
            sitekey_end = script_text.find("'", sitekey_start)
            sitekey = script_text[sitekey_start:sitekey_end]
            
            # Решаем капчу через TwoCaptcha
            token = solve_captcha(sitekey, url)
            token = token['code']
            if token:
                print(f"Токен капчи: {token}")
                # Вставляем токен в textarea
                await page.evaluate(f'''
                    document.getElementById("g-recaptcha-response").value = "{token}";
                ''')
                
                # Выполняем AJAX-запрос и перенаправляем на исходный URL
                await page.evaluate(f'''
                    jQuery.ajax({{
                        url: "/validation_recaptcha.do?method=v2",
                        dataType: "json",
                        type: "POST",
                        data: {{
                            token: "{token}",
                        }},
                    }}).done(function(data) {{
                        if (data[0].success == true) {{
                            window.location.href = "{url}";
                        }} else {{
                            alert('Капча не решена, попробуйте позже.');
                        }}
                    }});
                ''')
                
                # Ждем перенаправления и загрузки страницы
                await asyncio.sleep(10)
                html = await page.get_content()
                print(f"HTML после капчи сохранен в index.html")
            else:
                print("Не удалось решить капчу")
                await browser.stop()
                return None
        else:
            print("Не удалось найти sitekey в HTML")
            await browser.stop()
            return None
    await browser.stop()
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    return html

def solve_captcha(sitekey: str, url: str):
    solver = TwoCaptcha(RUCAPTCHA_API_KEY)
    try:
        result = solver.recaptcha(sitekey=sitekey, url=url)
        print(f"Результат TwoCaptcha: {result}")
        return result
    except Exception as e:
        print(f"Ошибка при решении капчи: {e}")
        return None

# Функция для решения капчи через RuCaptcha
async def solve_recaptcha(sitekey: str, url: str, action: str):
    async with aiohttp.ClientSession() as session:
        response = await session.get(
            f'http://rucaptcha.com/in.php?key={RUCAPTCHA_API_KEY}&method=userrecaptcha&googlekey={sitekey}&pageurl={url}'
        )
        if response.status != 200:
            print(f"Ошибка запроса к RuCaptcha: {response.status}")
            return None
        request_id = (await response.text()).split('|')[1]
        for _ in range(20):
            response = await session.get(
                f'http://rucaptcha.com/res.php?key={RUCAPTCHA_API_KEY}&action=get&id={request_id}'
            )
            text = await response.text()
            if 'CAPCHA_NOT_READY' in text:
                await asyncio.sleep(5)
                continue
            elif 'OK' in text:
                return text.split('|')[1]
            else:
                print(f"Ошибка получения решения: {text}")
                return None
        print("Превышено время ожидания решения капчи")
        return None

# Парсинг основной информации о машинах
async def parse_cars(car_type: str):
    url = f"http://www.encar.com/dc/dc_carsearchlist.do?carType={car_type}"
    html = await get_html_content(url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    car_items = soup.select('ul.car_list > li')
    cars = []
    print(f"Найдено {len(car_items)} автомобилей")
    for item in car_items:
        try:
            link_elem = item.find('a', class_='newLink')
            carid = int(link_elem['href'].split('carid=')[1].split('&')[0])  # Преобразуем в int, так как id в модели — BigInteger
            full_link = f"http://www.encar.com{link_elem['href']}"
            cls = item.find('span', class_='cls')
            brand = cls.find('strong').text.strip()
            model = cls.find('em').text.strip()
            dtl = item.find('span', class_='dtl')
            modification = dtl.find('strong').text.strip()
            name = f"{brand} {model} {modification}"
            price_elem = item.find('span', class_='prc').find('strong')
            price = int(price_elem.text.replace(',', '')) * 10_000
            cars.append({
                "id": carid,  # Используем id вместо carid
                "name": name,
                "price_won": price,
                "url": full_link,
                "manufacture": brand,
                "model": model,
                "series": modification
            })
        except (AttributeError, IndexError, ValueError) as e:
            print(f"Ошибка парсинга элемента: {e}")
            continue
    return cars

# Парсинг детальной страницы автомобиля
async def parse_car_details(url: str):
    html = await get_html_content(url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    mileage_elem = soup.find('span', class_='mileage')
    mileage = int(mileage_elem.text.replace(',', '').replace('km', '')) if mileage_elem else None
    
    engine_type_elem = soup.find('span', class_='engine_type')
    engine_type = engine_type_elem.text.strip() if engine_type_elem else None
    
    drive_type_elem = soup.find('span', class_='drive_type')
    drive_type = drive_type_elem.text.strip() if drive_type_elem else None
    
    color_elem = soup.find('span', class_='color')
    car_color = color_elem.text.strip() if color_elem else None
    
    date_elem = soup.find('span', class_='release_date')
    date_release = datetime.strptime(date_elem.text.strip(), '%Y년 %m월') if date_elem else None
    
    equipment_elem = soup.find('span', class_='equipment')
    equipment = equipment_elem.text.strip() if equipment_elem else None
    
    return {
        'mileage': mileage,
        'engine_type': engine_type,
        'drive_type': drive_type,
        'car_color': car_color,
        'date_release': date_release,
        'equipment': equipment
    }

# Парсинг страховой истории
async def parse_accident_summary(carid: str):
    url = f"https://fem.encar.com/cars/report/accident/{carid}"
    html = await get_html_content(url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    summary = {}
    summary_list = soup.find('ul', class_='ReportAccidentSummary_list_accident__q6vLx')
    if summary_list:
        for li in summary_list.find_all('li'):
            title = li.find('strong', class_='ReportAccidentSummary_tit__oxjum').text.strip()
            value = li.find('span', class_='ReportAccidentSummary_txt__fVCew').text.strip()
            summary[title] = value
    
    result = {}
    ownership_text = summary.get('번호 / 소유자 변경이력', '')
    if ownership_text:
        parts = ownership_text.split()
        result['change_ownership'] = int(parts[1].replace('회', '')) if len(parts) >= 2 else None
    
    result['traffic_accident_owner'] = 0 if summary.get('보험사고 이력 (내차 피해)') == '없음' else 1
    result['traffic_accident_other'] = 0 if summary.get('보험사고 이력 (타차 가해)') == '없음' else 1
    result['all_traffic_accident'] = result['traffic_accident_owner'] + result['traffic_accident_other']
    
    special_history = summary.get('특수 사고이력', '')
    result['theft'] = 0 if '도난 0회' in special_history else 1
    result['flood'] = 0 if '침수 0회' in special_history else 1
    result['death'] = 0 if '전손 0회' in special_history else 1
    
    result['publication_dttm'] = datetime.now()
    result['check_dttm'] = datetime.now()
    
    return result

# Основная функция парсинга
async def parse_full_car_info(car_type: str):
    exchange_rate = await get_exchange_rate()
    cars_basic = await parse_cars(car_type)
    
    async with DBApi() as db:
        for car in cars_basic:
            car_id = car['id']  # id теперь является carid
            
            # Проверяем, существует ли автомобиль
            existing_car = await db.get_car_by_id(car_id)
            if existing_car:
                print(f"Автомобиль с id={car_id} уже существует, пропускаем")
                continue
            
            # Собираем дополнительные данные
            details = await parse_car_details(car['url'])
            car.update(details)
            
            accident_data = await parse_accident_summary(str(car_id))  # Передаем carid как строку
            car.update(accident_data)
            
            # Получаем или создаем записи в справочниках
            manufacture = await db.get_manufacture_by_name(car['manufacture'])
            if not manufacture:
                manufacture = await db.create_manufacture(car['manufacture'])
            car['manufacture_id'] = manufacture.id
            
            model = await db.get_model_by_name(car['model'])
            if not model:
                model = await db.create_model(manufacture_id=car['manufacture_id'], name=car['model'])
            car['model_id'] = model.id
            
            series = await db.get_series_by_name(car['series'])
            if not series:
                series = await db.create_series(models_id=car['model_id'], name=car['series'])
            car['series_id'] = series.id
            
            equipment = car.get('equipment')
            if equipment:
                equip = await db.get_equipment_by_name(equipment)
                if not equip:
                    equip = await db.create_equipment(series_id=car['series_id'], name=equipment)
                car['equipment_id'] = equip.id
            else:
                car['equipment_id'] = None
            
            engine_type = car.get('engine_type')
            if engine_type:
                eng_type = await db.get_engine_type_by_name(engine_type)
                if not eng_type:
                    eng_type = await db.create_engine_type(engine_type)
                car['engine_type_id'] = eng_type.id
            else:
                car['engine_type_id'] = None
            
            drive_type = car.get('drive_type')
            if drive_type:
                drv_type = await db.get_drive_type_by_name(drive_type)
                if not drv_type:
                    drv_type = await db.create_drive_type(drive_type)
                car['drive_type_id'] = drv_type.id
            else:
                car['drive_type_id'] = None
            
            car_color = car.get('car_color')
            if car_color:
                color = await db.get_car_color_by_name(car_color)
                if not color:
                    color = await db.create_car_color(car_color)
                car['car_color_id'] = color.id
            else:
                car['car_color_id'] = None
            
            car['price_rub'] = int(car['price_won'] * exchange_rate) if car['price_won'] else None
            
            # Подготовка данных для создания записи
            car_data = {
                'id': car['id'],  # Используем id как carid
                'manufacture_id': car['manufacture_id'],
                'model_id': car['model_id'],
                'series_id': car['series_id'],
                'equipment_id': car['equipment_id'],
                'engine_type_id': car['engine_type_id'],
                'drive_type_id': car['drive_type_id'],
                'car_color_id': car['car_color_id'],
                'mileage': car.get('mileage'),
                'price_won': car['price_won'],
                'price_rub': car['price_rub'],
                'date_release': car.get('date_release'),
                'publication_dttm': car.get('publication_dttm'),
                'check_dttm': car.get('check_dttm'),
                'change_ownership': car.get('change_ownership'),
                'all_traffic_accident': car.get('all_traffic_accident'),
                'traffic_accident_owner': car.get('traffic_accident_owner'),
                'traffic_accident_other': car.get('traffic_accident_other'),
                'theft': car.get('theft'),
                'flood': car.get('flood'),
                'death': car.get('death'),
                'url': car['url']
            }
            
            # Создаем запись в базе данных
            await db.create_car(**car_data)
            print(f"Добавлен автомобиль с id={car_id}")

# Запуск парсера
if __name__ == "__main__":
    res = asyncio.run(parse_cars('kor'))
    print(res)