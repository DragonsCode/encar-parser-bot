from curl_cffi import requests
from bs4 import BeautifulSoup

def parse_cars():
    url = "http://www.encar.com/dc/dc_carsearchlist.do?carType=kor"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, impersonate="chrome", headers=headers)
    print(response.text)
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    car_items = soup.select('ul.car_list > li')  # Все <li> внутри <ul class="car_list">
    cars = []

    for item in car_items:
        try:
            # Ссылка и carid
            link_elem = item.find('a', class_='newLink')
            carid = link_elem['href'].split('carid=')[1].split('&')[0]
            full_link = f"http://www.encar.com{link_elem['href']}"

            # Название: бренд + модель + модификация
            cls = item.find('span', class_='cls')
            brand = cls.find('strong').text.strip()
            model = cls.find('em').text.strip()
            dtl = item.find('span', class_='dtl')
            modification = dtl.find('strong').text.strip()
            name = f"{brand} {model} {modification}"

            # Цена
            price_elem = item.find('span', class_='prc').find('strong')
            price = int(price_elem.text.replace(',', '')) * 10_000  # Переводим 만원 в won

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