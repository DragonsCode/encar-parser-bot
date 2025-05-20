from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging
import os
import pickle
import zendriver as zd

# Единый User-Agent для согласованности с парсером
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0"

async def save_cookies(browser: zd.Browser):
    """Сохраняет куки в файл в формате pickle."""
    os.makedirs("cookies", exist_ok=True)
    cookie_file = "cookies/encar_cookies.dat"
    cookies = await browser.cookies.get_all()  # Получаем все cookies
    with open(cookie_file, "wb") as f:
        pickle.dump(cookies, f)  # Сохраняем в бинарном формате
    print("Cookies успешно сохранены.")

async def refresh_cookies():
    """Обновляет cookies, запуская браузер и сохраняя новые cookies."""
    browser = await zd.start(headless=True, user_agent=USER_AGENT)
    page = await browser.get('https://car.encar.com/list/car?page=1&search=%7B%22type%22%3A%22ev%22%2C%22action%22%3A%22(And.Hidden.N._.CarType.A._.GreenType.Y.)%22%2C%22title%22%3A%22%EC%A0%84%EA%B8%B0%C2%B7%EC%B9%9C%ED%99%98%EA%B2%BD%22%2C%22toggle%22%3A%7B%7D%2C%22layer%22%3A%22%22%2C%22sort%22%3A%22MobileModifiedDate%22%7D')
    await page.wait(30)  # Ждём 30 секунд для загрузки страницы
    await save_cookies(browser)
    await browser.stop()
    print("Cookies обновлены.")

async def run_scheduler():
    """Запускает планировщик для периодического обновления cookies."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_cookies, 'interval', hours=5)
    scheduler.start()

    # Держим событийный цикл активным
    try:
        await asyncio.Event().wait()  # Бесконечное ожидание
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Планировщик остановлен")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scheduler())