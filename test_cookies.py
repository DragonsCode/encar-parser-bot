import asyncio
import aiohttp
import requests
import pickle
import json
import random
import os
import zendriver as zd
from zendriver import Tab, Browser, Element

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0"
# Список User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

def get_random_headers():
    """Возвращает случайные заголовки с User-Agent."""
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://car.encar.com/",
        "User-Agent": USER_AGENT
        # "User-Agent": random.choice(USER_AGENTS)
    }

async def save_cookies(browser: Browser):
    """Сохраняет куки в файл в формате pickle."""
    os.makedirs("cookies", exist_ok=True)
    cookie_file = "cookies/encar_cookies.dat"
    cookies = await browser.cookies.get_all()  # Получаем все cookies
    with open(cookie_file, "wb") as f:
        pickle.dump(cookies, f)  # Сохраняем в бинарном формате
    print("Cookies успешно сохранены.")

async def load_cookies():
    """Загружает куки из файла."""
    cookie_file = "cookies/encar_cookies.dat"
    if os.path.exists(cookie_file):
        with open(cookie_file, "rb") as f:
            cookies = pickle.load(f)  # Загружаем cookies как объект Python
        print("Cookies успешно загружены.")
        return cookies
    print("Файл cookies не найден.")
    return None

async def get_browser():
    """Запускает браузер, получает cookies и сохраняет их."""
    browser = await zd.start(headless=True, user_agent=USER_AGENT)
    page = await browser.get('https://car.encar.com/list/car?page=1&search=%7B%22type%22%3A%22ev%22%2C%22action%22%3A%22(And.Hidden.N._.CarType.A._.GreenType.Y.)%22%2C%22title%22%3A%22%EC%A0%84%EA%B8%B0%C2%B7%EC%B9%9C%ED%99%98%EA%B2%BD%22%2C%22toggle%22%3A%7B%7D%2C%22layer%22%3A%22%22%2C%22sort%22%3A%22MobileModifiedDate%22%7D')
    await page.wait(30)
    await save_cookies(browser)
    await browser.stop()

async def fetch_api_data(url: str, params: dict = None, retries: int = 3):
    """Получает данные из API с использованием cookies и повторными попытками."""
    cookies = await load_cookies()
    if not cookies:
        print("Cookies не найдены, получаем новые.")
        await get_browser()
        cookies = await load_cookies()
        if not cookies:
            raise Exception("Не удалось получить cookies.")

    # Преобразуем cookies в формат словаря для aiohttp
    cookie_jar = {cookie['name']: cookie['value'] for cookie in cookies}

    for attempt in range(retries):
        headers = get_random_headers()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, headers=headers, cookies=cookie_jar, timeout=10) as response:
                    print(f"Запрос к {url} (попытка {attempt + 1}): статус {response.status}")
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 407:
                        print(f"Ошибка 407: {await response.text()}")
                        if attempt == retries - 1:
                            print("Обновляем cookies после неудачных попыток.")
                            await get_browser()
                            cookies = await load_cookies()
                            if cookies:
                                cookie_jar = {cookie['name']: cookie['value'] for cookie in cookies}
                        await asyncio.sleep(2 ** attempt)
                    else:
                        print(f"Ошибка {response.status}: {await response.text()}")
                        return None
            except Exception as e:
                print(f"Исключение при запросе (попытка {attempt + 1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
    print(f"Не удалось получить данные после {retries} попыток.")
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
        
        data = await fetch_api_data(base_url, params)
        if not data or 'SearchResults' not in data or not data['SearchResults']:
            print(f"Страница {page_num} не содержит машин, завершаем парсинг {car_type}.")
            break
        
        total_count = data.get('Count', 0)
        print(f"Страница {page_num}: найдено {len(data['SearchResults'])} машин, всего доступно {total_count}")
        
        yield data['SearchResults']
        
        offset += page_size
        page_num += 1
        await asyncio.sleep(1)

async def main():
    """Основная функция для тестирования парсера."""
    async for cars in parse_cars("kor", max_pages=2):
        print(f"Получено {len(cars)} машин на странице.")

async def test():
    """Тестирует сохранение и загрузку cookies, а также запрос через requests."""
    await get_browser()
    print("Cookies успешно сохранены.")

    cookies = await load_cookies()
    if cookies:
        print("Cookies успешно загружены.")
        # Преобразуем cookies в формат для requests
        cookies_dict = {cookie.name: cookie.value for cookie in cookies}
        url = "https://api.encar.com/search/car/list/mobile"
        params = {
            "count": "true",
            "q": "(And.Hidden.N._.CarType.A._.GreenType.Y.)",
            "sr": f"|MobileModifiedDate|0|200",
            "inav": "|Metadata|Sort",
            "cursor": ""
        }
        headers = get_random_headers()
        response = requests.get(url, params=params, headers=headers, cookies=cookies_dict)
        print(f"Статус запроса: {response.status_code}")
        if response.status_code == 200:
            print("Запрос через requests успешен.")
            data = response.json()
            print(f"Получено {len(data['SearchResults'])} машин.")
        else:
            print(f"Ошибка запроса: {response.status_code} - {response.text}")
    else:
        print("Не удалось загрузить cookies.")

if __name__ == "__main__":
    asyncio.run(test())