import hashlib
from typing import Dict
from database import DBApi

# Ключи для обращения к настройкам в базе данных
INTELLECTMONEY_KEYS = {
    "bearer_token": "intellectmoney_bearer_token",
    "sign_secret_key": "intellectmoney_sign_secret_key",
    "eshop_secret_key": "intellectmoney_eshop_secret_key",
    "eshop_id": "intellectmoney_eshop_id"
}

async def get_intellectmoney_setting(key: str, db: DBApi) -> str:
    """Получение значения настройки IntellectMoney из базы данных."""
    setting_key = INTELLECTMONEY_KEYS.get(key)
    if not setting_key:
        raise ValueError(f"Неизвестный ключ IntellectMoney: {key}")
    
    setting = await db.get_setting_by_key(setting_key)
    if not setting or not setting.value:
        raise ValueError(f"Настройка {setting_key} не найдена в базе данных или пуста")
    return setting.value

async def get_intellectmoney_keys(db: DBApi) -> Dict[str, str]:
    """Получение всех ключей IntellectMoney из базы данных."""
    return {
        "bearer_token": await get_intellectmoney_setting("bearer_token", db),
        "sign_secret_key": await get_intellectmoney_setting("sign_secret_key", db),
        "eshop_secret_key": await get_intellectmoney_setting("eshop_secret_key", db),
        "eshop_id": await get_intellectmoney_setting("eshop_id", db)
    }

def generate_sign_hash(params: Dict[str, str], template: str, sign_secret_key: str) -> str:
    """Генерация хеша для заголовка Sign."""
    params_with_secret = {**params, "signSecretKey": sign_secret_key}
    sign_string = template.format(**params_with_secret)
    return hashlib.sha256(sign_string.encode("utf-8")).hexdigest()

def generate_param_hash(params: Dict[str, str], template: str, eshop_secret_key: str) -> str:
    """Генерация хеша для параметра hash."""
    params_with_secret = {**params, "secretKey": eshop_secret_key}
    hash_string = template.format(**params_with_secret)
    return hashlib.md5(hash_string.encode("utf-8")).hexdigest()