import zendriver as zd
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from datetime import datetime
from twocaptcha import TwoCaptcha
from database import DBApi
import urllib.parse
import re

# Ваш API-ключ от RuCaptcha
RUCAPTCHA_API_KEY = '5568f74281346b5ec0124237ff51da51'  # Замените на реальный ключ

# Глобальный браузер
browser = None

async def init_browser():
    """Инициализирует глобальный браузер."""
    global browser
    browser = await zd.start(headless=False)

async def close_browser():
    """Закрывает глобальный браузер."""
    global browser
    if browser:
        await browser.stop()

# Функция для получения курса валют (KRW -> RUB)
async def get_exchange_rate():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.exchangerate-api.com/v4/latest/KRW') as response:
            data = await response.json()
            return data['rates']['RUB']

# Основная функция для получения HTML с обработкой капчи
async def get_html_content(base_url: str, params: dict = None):
    global browser
    url = base_url if not params else f"{base_url}?{urllib.parse.urlencode(params)}"
    page = await browser.get(url)
    await asyncio.sleep(10)
    html = await page.get_content()

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    if "recaptcha" in html.lower():
        print("Обнаружена reCAPTCHA v2, решаем капчу...")
        soup = BeautifulSoup(html, 'html.parser')
        
        script_tag = soup.find('script', string=lambda text: text and 'grecaptcha.render' in text)
        if script_tag:
            script_text = script_tag.string
            sitekey_start = script_text.find("'sitekey' : '") + len("'sitekey' : '")
            sitekey_end = script_text.find("'", sitekey_start)
            sitekey = script_text[sitekey_start:sitekey_end]
            
            token = solve_captcha(sitekey, url)
            token = token['code'] if token else None
            if token:
                print(f"Токен капчи: {token}")
                await page.evaluate(f'document.getElementById("g-recaptcha-response").value = "{token}";')
                await page.evaluate(f'''
                    jQuery.ajax({{
                        url: "/validation_recaptcha.do?method=v2",
                        dataType: "json",
                        type: "POST",
                        data: {{ token: "{token}" }},
                    }}).done(function(data) {{
                        if (data[0].success == true) {{
                            window.location.href = "{url}";
                        }} else {{
                            alert('Капча не решена, попробуйте позже.');
                        }}
                    }});
                ''')
                await asyncio.sleep(10)
                html = await page.get_content()
            else:
                print("Не удалось решить капчу")
                return None
    
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

# Парсинг списка автомобилей
async def parse_cars(car_type: str, max_pages: int = None):
    """
    Парсит список автомобилей с мобильной версии сайта с учетом пагинации.
    
    Аргументы:
        car_type (str): Тип автомобилей ('kor' для обычных, 'ev' для электро).
        max_pages (int, optional): Максимальное количество страниц для парсинга.
    
    Возвращает:
        list: Список словарей с базовой информацией об автомобилях.
    """
    base_url = "https://car.encar.com/list/car"
    if car_type == 'kor':
        type_car = "car"
        action = "(And.Hidden.N._.CarType.A.)"
        title = "국산·수입"
    elif car_type == 'ev':
        type_car = "ev"
        action = "(And.Hidden.N._.CarType.A._.GreenType.Y.)"
        title = "수입"
    else:
        raise ValueError("Неверный car_type. Используйте 'kor' или 'ev'.")
    
    search = f'{{"type":"{type_car}","action":"{action}","title":"{title}","toggle":{{}},"layer":"","sort":"MobileModifiedDate"}}'
    page = 1
    all_cars = []
    
    while True:
        if max_pages and page > max_pages:
            break
        params = {"page": page, "search": search}
        html = await get_html_content(base_url, params)
        if not html:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        car_items = soup.select('.ItemBigImage_item__6bPnX')
        if not car_items:
            print(f"Страница {page} не содержит автомобилей, завершаем парсинг.")
            break
        
        print(f"Найдено {len(car_items)} автомобилей на странице {page}")
        for item in car_items:
            try:
                link_elem = item.find('a')
                carid = int(link_elem['href'].split('/detail/')[1].split('?')[0])
                full_link = f"https://car.encar.com{link_elem['href']}"
                name_elem = item.find('strong', class_='ItemBigImage_name__h0biK')
                name = name_elem.text.strip() if name_elem else "Не указано"
                info_elems = item.find('ul', class_='ItemBigImage_info__YMI5y').find_all('li')
                year = info_elems[0].text.strip() if len(info_elems) > 0 else None
                mileage = int(info_elems[1].text.strip().replace(',', '').replace('km', '')) if len(info_elems) > 1 else None
                fuel = info_elems[2].text.strip() if len(info_elems) > 2 else None
                region = info_elems[3].text.strip() if len(info_elems) > 3 else None
                price_elem = item.find('span', class_='ItemBigImage_num__Fu15_')
                price = int(price_elem.text.strip().replace(',', '')) * 10_000 if price_elem else None
                
                all_cars.append({
                    "id": carid,
                    "name": name,
                    "year": year,
                    "mileage": mileage,
                    "fuel": fuel,
                    "region": region,
                    "price_won": price,
                    "url": full_link
                })
            except (AttributeError, IndexError, ValueError) as e:
                print(f"Ошибка парсинга элемента на странице {page}: {e}")
                continue
        
        page += 1
        await asyncio.sleep(2)
    
    return all_cars

# Парсинг деталей автомобиля
async def parse_car_details(url: str):
    html = await get_html_content(url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Пробег (mileage)
    mileage_elem = soup.find('dd', text=re.compile(r'\d+,\d+km'))
    mileage = int(mileage_elem.text.replace(',', '').replace('km', '')) if mileage_elem else None
    
    # Тип двигателя (engine_type) — предполагаем, что это тип топлива
    engine_type_elem = soup.find('dd', text=re.compile(r'가솔린|디젤|전기|하이브리드'))
    engine_type = engine_type_elem.text.strip() if engine_type_elem else None
    
    # Тип привода (drive_type) — не найден в HTML, оставляем None
    drive_type = None  # Можно добавить логику поиска, если данные появятся
    
    # Цвет автомобиля (car_color) — извлекаем из мета-тега
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    car_color = None
    if meta_desc:
        match = re.search(r'색상:(\w+)', meta_desc['content'])
        if match:
            car_color = match.group(1)
    
    # Дата выпуска (date_release)
    date_elem = soup.find('dd', text=re.compile(r'\d{2}/\d{2}식'))
    date_release = None
    if date_elem:
        date_str = date_elem.text.split('식')[0].strip()  # Берем "18/03" из "18/03식"
        year, month = map(int, date_str.split('/'))
        date_release = datetime(2000 + year, month, 1)  # Преобразуем в datetime, добавляем 2000 к двухзначному году
    
    # Оборудование (equipment) — список опций
    equipment_list = soup.find('ul', class_='DetailOption_list_option__kTYgR')
    equipment = []
    if equipment_list:
        for li in equipment_list.find_all('li', class_='DetailOption_on__CfAJf'):
            equipment.append(li.text.strip())
    
    return {
        'mileage': mileage,
        'engine_type': engine_type,
        'drive_type': drive_type,
        'car_color': car_color,
        'date_release': date_release,
        'equipment': ', '.join(equipment) if equipment else None
    }

# Парсинг страховой истории
async def parse_accident_summary(carid: str):
    url = f"https://fem.encar.com/cars/report/accident/{carid}"
    html = await get_html_content(url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Извлечение summary
    summary = {}
    summary_list = soup.find('ul', class_='ReportAccidentSummary_list_accident__q6vLx')
    if summary_list:
        for li in summary_list.find_all('li'):
            title = li.find('strong', class_='ReportAccidentSummary_tit__oxjum').text.strip()
            value = li.find('span', class_='ReportAccidentSummary_txt__fVCew').text.strip()
            summary[title] = value
    
    result = {}
    
    # Количество смен владельцев
    ownership_text = summary.get('번호 / 소유자 변경이력', '')
    if ownership_text:
        match = re.search(r'(\d+)회$', ownership_text)
        result['change_ownership'] = int(match.group(1)) if match else None
    
    # Страховые случаи: ущерб своему авто
    traffic_owner_text = summary.get('보험사고 이력 (내차 피해)', '')
    result['traffic_accident_owner'] = 0 if traffic_owner_text == '없음' else 1
    
    # Страховые случаи: ущерб чужому авто
    traffic_other_text = summary.get('보험사고 이력 (타차 가해)', '')
    result['traffic_accident_other'] = 0 if traffic_other_text == '없음' else 1
    
    # Общее количество страховых случаев
    result['all_traffic_accident'] = result['traffic_accident_owner'] + result['traffic_accident_other']
    
    # Специальные случаи
    special_history = summary.get('특수 사고이력', '')
    if special_history:
        result['theft'] = 0 if '도난 0회' in special_history else 1
        result['flood'] = 0 if '침수(전손,분손) 0회' in special_history else 1
        result['death'] = 0 if '전손 0회' in special_history else 1
    else:
        result['theft'] = None
        result['flood'] = None
        result['death'] = None
    
    try:
        # Дата проверки (check_dttm) из <dd> с "2025/01/31"
        check_date_elem = soup.find('dd', class_='ReportAccidentSummary_txt__fVCew')
        if check_date_elem:
            check_date_str = check_date_elem.text.strip()  # "2025/01/31"
            result['check_dttm'] = datetime.strptime(check_date_str, '%Y/%m/%d')
        else:
            result['check_dttm'] = None
    except:
        # Дата проверки (check_dttm) из <dd> после "정보조회일"
        check_date_elem = soup.find('dt', string='정보조회일')
        if check_date_elem:
            check_date_str = check_date_elem.find_next_sibling('dd').text.strip()  # "2025/01/31"
            result['check_dttm'] = datetime.strptime(check_date_str, '%Y/%m/%d')
        else:
            result['check_dttm'] = None
    
    try:
        # Дата публикации (publication_dttm) из <span class="ReportAccidentInfo_date__oweNo">
        publication_date_elem = soup.find('span', class_='ReportAccidentInfo_date__oweNo')
        if publication_date_elem:
            publication_date_str = publication_date_elem.text.split(' ')[-1]  # "2025-01-31"
            result['publication_dttm'] = datetime.strptime(publication_date_str, '%Y-%m-%d')
        else:
            result['publication_dttm'] = None
    except:
        # Дата публикации (publication_dttm) из <span class="ReportAccidentInfo_date__oweNo">
        publication_date_elem = soup.find('span', class_='ReportAccidentInfo_date__oweNo')
        if publication_date_elem:
            publication_date_str = publication_date_elem.text.strip()  # "2025년 01월 31일"
            result['publication_dttm'] = datetime.strptime(publication_date_str, '%Y년 %m월 %d일')
        else:
            result['publication_dttm'] = None
    
    return result

# Параллельный парсинг деталей и страховки с семафором
async def fetch_car_full_info(car, exchange_rate, sem: asyncio.Semaphore):
    async with sem:  # Ограничиваем доступ к задаче с помощью семафора
        try:
            car['url'] = car['url'].replace('https://car.encar.com', '')
            details = await parse_car_details(car['url'])
            car.update(details)
            
            accident_data = await parse_accident_summary(str(car['id']))
            car.update(accident_data)
            
            # Здесь предполагается, что поля manufacture, model, series нужно извлечь из name
            # Для простоты можно разбить name, но лучше уточнить структуру
            name_parts = car['name'].split(maxsplit=2)
            manufacture_name = name_parts[0] if len(name_parts) > 0 else "Unknown"
            model_name = name_parts[1] if len(name_parts) > 1 else "Unknown"
            series_name = name_parts[2] if len(name_parts) > 2 else "Unknown"
            
            async with DBApi() as db:
                manufacture = await db.get_manufacture_by_name(manufacture_name)
                if not manufacture:
                    manufacture = await db.create_manufacture(manufacture_name)
                car['manufacture_id'] = manufacture.id
                
                model = await db.get_model_by_name(model_name)
                if not model:
                    model = await db.create_model(manufacture_id=car['manufacture_id'], name=model_name)
                car['model_id'] = model.id
                
                series = await db.get_series_by_name(series_name)
                if not series:
                    series = await db.create_series(models_id=car['model_id'], name=series_name)
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
                
                car_data = {
                    'id': car['id'],
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
                
                await db.create_car(**car_data)
                print(f"Добавлен автомобиль с id={car['id']}")
        except Exception as e:
            print(f"Ошибка при обработке автомобиля {car['id']}: {e}")

# Основная функция с многозадачностью и семафором
async def parse_full_car_info(car_type: str, max_pages: int = None):
    await init_browser()
    try:
        exchange_rate = await get_exchange_rate()
        cars_basic = await parse_cars(car_type, max_pages)
        
        # Создаем семафор с лимитом 5 параллельных задач
        sem = asyncio.Semaphore(5)
        
        # Создаем задачи с использованием семафора
        tasks = [fetch_car_full_info(car, exchange_rate, sem) for car in cars_basic]
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        await close_browser()

# Запуск парсера
if __name__ == "__main__":
    asyncio.run(parse_full_car_info('kor', max_pages=1))