import nodriver as uc
from bs4 import BeautifulSoup
import time

async def parse_cars():
    url = "http://www.encar.com/dc/dc_carsearchlist.do?carType=kor"
    
    browser = await uc.start(headless=True)
    page = await browser.get(url)
    # time.sleep(5)  # Ждем загрузки страницы
    await page.sleep(10)
    html = await page.get_content()
    
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
    cars = uc.loop().run_until_complete(parse_cars())
    for car in cars:
        print(f"ID: {car['carid']}, Название: {car['name']}, Цена: {car['price']} won, Ссылка: {car['link']}")