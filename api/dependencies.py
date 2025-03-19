# api/dependencies.py
from fastapi import Header, HTTPException, Depends
from aiogram.utils.web_app import safe_parse_webapp_init_data
from database import DBApi
from typing import Optional

async def get_telegram_user(auth: str = Header(...)):
    """Проверяет авторизацию через Telegram и возвращает user_id."""
    async with DBApi() as db:
        setting = await db.get_setting_by_key("telegram_bot_token")
        test_setting = await db.get_setting_by_key("test_token")
        if not setting or not setting.value:
            raise HTTPException(status_code=500, detail="Токен Telegram бота не настроен")
        bot_token = setting.value

    if auth == test_setting.value:
        return 235519518
    
    try:
        web_app_data = safe_parse_webapp_init_data(token=bot_token, init_data=auth)
        user_id = web_app_data.user.id
        return user_id
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверные данные авторизации Telegram")

async def get_admin_token(auth: str = Header(...), login: str = Header(...)):
    """Проверяет авторизацию админа через токен."""
    async with DBApi() as db:
        setting = await db.get_setting_by_key("admin_token")
        login = await db.get_setting_by_key("admin_login")
        if not setting or not setting.value or not login or not login.value:
            raise HTTPException(status_code=500, detail="Данные админа не настроены")
        if auth != setting.value or login.value != login:
            raise HTTPException(status_code=403, detail="Неверные данные админа")
    
    return True

# Пример использования в эндпоинтах
async def telegram_auth(user_id: int = Depends(get_telegram_user)):
    return user_id

async def admin_auth(is_admin: bool = Depends(get_admin_token)):
    return is_admin