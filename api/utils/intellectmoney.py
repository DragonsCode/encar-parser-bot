import hashlib
from typing import Dict
from database import DBApi
from urllib.parse import unquote, unquote_plus
import unicodedata

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

def generate_callback_hash(params: dict, secret_key: str) -> str:
    fields = [
        params.get("eshopId", ""),
        params.get("orderId", ""),
        unquote_plus(params.get("serviceName", ""), encoding="windows-1251", errors="replace"),
        params.get("eshopAccount", ""),
        params.get("recipientAmount", ""),
        params.get("recipientCurrency", ""),
        params.get("paymentStatus", ""),
        unquote_plus(params.get("userName", ""), encoding="windows-1251", errors="replace"),
        unquote_plus(params.get("userEmail", ""), encoding="windows-1251", errors="replace"),
        unquote_plus(params.get("paymentData", ""), encoding="windows-1251", errors="replace"),
        secret_key
    ]
    # Normalize Unicode and create the hash string
    # fields = [unicodedata.normalize("NFC", field) for field in fields]
    hash_string = "::".join(fields)
    print("Callback hash string:", hash_string)
    try:
        hash_bytes = hash_string.encode("windows-1251")
    except UnicodeEncodeError as e:
        print(f"Encoding error: {e}")
        hash_string = hash_string.encode("windows-1251", errors="replace").decode("windows-1251")
        hash_bytes = hash_string.encode("windows-1251")
    hash_object = hashlib.md5(hash_bytes)
    return hash_object.hexdigest()

def generate_sign_hash(params: Dict[str, str], template: str, sign_secret_key: str) -> str:
    """Генерация хеша для заголовка Sign."""
    # Формируем строку, заменяя параметры в шаблоне
    sign_string = template.format(
        eshopId=params.get("eshopId", ""),
        orderId=params.get("orderId", ""),
        serviceName=params.get("serviceName", ""),
        recipientAmount=params.get("recipientAmount", ""),
        recipientCurrency=params.get("recipientCurrency", ""),
        userName=params.get("userName", ""),
        email=params.get("email", ""),
        successUrl=params.get("successUrl", ""),
        failUrl=params.get("failUrl", ""),
        backUrl=params.get("backUrl", ""),
        resultUrl=params.get("resultUrl", ""),
        expireDate=params.get("expireDate", ""),
        holdMode=params.get("holdMode", ""),
        preference=params.get("preference", ""),
        signSecretKey=sign_secret_key
    )
    print("Sign string:", sign_string)  # Для отладки
    # Кодируем строку в UTF-8 и вычисляем SHA256
    sign_bytes = sign_string.encode("utf-8")
    hash_object = hashlib.sha256(sign_bytes)
    sign_hash = hash_object.hexdigest()
    return sign_hash

def generate_param_hash(params: Dict[str, str], template: str, eshop_secret_key: str) -> str:
    """Генерация хеша для параметра hash."""
    # Формируем строку, заменяя параметры в шаблоне
    hash_string = template.format(
        eshopId=params.get("eshopId", ""),
        orderId=params.get("orderId", ""),
        serviceName=params.get("serviceName", ""),
        recipientAmount=params.get("recipientAmount", ""),
        recipientCurrency=params.get("recipientCurrency", ""),
        userName=params.get("userName", ""),
        email=params.get("email", ""),
        successUrl=params.get("successUrl", ""),
        failUrl=params.get("failUrl", ""),
        backUrl=params.get("backUrl", ""),
        resultUrl=params.get("resultUrl", ""),
        expireDate=params.get("expireDate", ""),
        holdMode=params.get("holdMode", ""),
        preference=params.get("preference", ""),
        secretKey=eshop_secret_key
    )
    print("Hash string:", hash_string)  # Для отладки
    # Кодируем строку в UTF-8 и вычисляем SHA256
    hash_bytes = hash_string.encode("utf-8")
    hash_object = hashlib.md5(hash_bytes)
    param_hash = hash_object.hexdigest()
    return param_hash