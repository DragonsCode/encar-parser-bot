from playwright.sync_api import sync_playwright
from undetected_playwright import Tarnished
from bs4 import BeautifulSoup
import time

def parse_cars():
    url = "http://www.encar.com/dc/dc_carsearchlist.do?carType=kor"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # context = browser.new_context(
        #     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        #     viewport={"width": 1280, "height": 800}
        # )
        context = browser.new_context(locale="en-US")
        Tarnished.apply_stealth(context)
        page = context.new_page()
        page.goto(url, wait_until="networkidle")
        time.sleep(10)  # Ждем загрузки страницы
        html = page.content()
        browser.close()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    if "recaptcha" in html.lower():
        print("Обнаружена reCAPTCHA")
        return []
    
    car_items = soup.select('ul.car_list > li')
    cars = []
    for item in car_items:
        try:
            link_elem = item.find('a', class_='newLink')
            carid = link_elem['href'].split('carid=')[1].split('&')[0]
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
                "carid": carid,
                "name": name,
                "price": price,
                "link": full_link
            })
        except (AttributeError, IndexError, ValueError) as e:
            print(f"Ошибка парсинга элемента: {e}")
            continue
    return cars

if __name__ == "__main__":
    cars = parse_cars()
    for car in cars:
        print(f"ID: {car['carid']}, Название: {car['name']}, Цена: {car['price']} won, Ссылка: {car['link']}")