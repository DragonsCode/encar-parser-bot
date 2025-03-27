from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from api.dependencies import admin_auth
from api.models import PayHistoryCreate
from api.utils.intellectmoney import get_intellectmoney_keys, generate_sign_hash, generate_param_hash, generate_callback_hash
from database import DBApi
import requests
import cgi
from urllib.parse import unquote

router = APIRouter(prefix="/payhistory", tags=["PayHistory"])

class PaymentCreate(BaseModel):
    user_id: int
    tariff_id: int
    price: int
    email: str
    description: str = "Оплата подписки"

async def decode_body(request: Request) -> str:
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    _, options = cgi.parse_header(content_type)
    encoding = options.get("charset", "utf-8")
    print("ENCODING: ", encoding)
    # Декодируем тело в строку с указанной кодировкой
    decoded_body = body.decode(encoding)
    print("DECODED BODY: ", decoded_body)
    # Применяем unquote к декодированной строке
    return decoded_body  # unquote не нужен здесь, так как мы будем декодировать параметры позже

@router.post("/callback")
async def payment_callback(request: Request):
    """Обработка уведомлений от IntellectMoney."""
    print("CALLBACK")
    print("QUERY PARAMS: ", request.query_params)
    print("PATH PARAMS: ", request.path_params)
    body = await request.body()
    print("CALLBACK BODY: ", body)

    # Парсим данные как form-data
    form_data = await request.form()
    print("CALLBACK FORM DATA: ", form_data)

    # Извлекаем параметры
    invoice_id = form_data.get("paymentId")
    payment_status = form_data.get("paymentStatus")

    if not invoice_id or not payment_status:
        raise HTTPException(status_code=400, detail="Отсутствуют обязательные параметры paymentId или paymentStatus")

    # Проверяем подпись (hash)
    secret_key = form_data.get("secretKey", "")  # Используем secretKey из callback
    async with DBApi() as db:
        intellect_secrets = await get_intellectmoney_keys(db)
        secret_key = intellect_secrets["eshop_secret_key"]
    received_hash = form_data.get("hash")

    # Формируем параметры для проверки хеша, используя закодированные значения
    raw_params = dict()
    body_str = await decode_body(request)
    print("BODY STR: ", body_str)
    for pair in body_str.split("&"):
        key, value = pair.split("=", 1)
        raw_params[key] = value
    print("RAW PARAMS: ", raw_params)

    expected_hash = generate_callback_hash(raw_params, secret_key)
    print("EXPECTED HASH: ", expected_hash)
    print("RECEIVED HASH: ", received_hash)

    if received_hash != expected_hash:
        raise HTTPException(status_code=400, detail="Неверная подпись (hash)")

    # Обрабатываем статус платежа
    async with DBApi() as db:
        if payment_status == "5":  # Успешно оплачено
            await db.update_payhistory_by_invoice(invoice_id, successfully=True)
        elif payment_status in ["6", "7"]:  # Ошибка или отклонён
            pass

    # Возвращаем ответ "OK" согласно документации
    return "OK"

@router.post("/create")
async def create_payment(payment: PaymentCreate):
    """Создание платежа через IntellectMoney."""
    # Создаём запись в истории платежей
    pay_data = PayHistoryCreate(
        id=0,  # ID будет сгенерирован базой
        user_id=payment.user_id,
        tariff_id=payment.tariff_id,
        price=payment.price,
        successfully=False
    )
    async with DBApi() as db:
        success = await db.create_pay_history(**pay_data.model_dump())
        if not success:
            raise HTTPException(status_code=400, detail="Ошибка создания записи оплаты")
        pay_record = await db.get_last_payhistory_by_user(payment.user_id)  # Предполагается, что такой метод есть

        # Получаем ключи IntellectMoney
        keys = await get_intellectmoney_keys(db)

    # Параметры для IntellectMoney
    order_id = f"order_{pay_record.id}"
    params = {
        "eshopId": keys["eshop_id"],
        "orderId": order_id,
        "serviceName": payment.description,
        "recipientAmount": f"{payment.price:.2f}",
        "recipientCurrency": "TST",
        "userName": "",
        "email": payment.email,
        "successUrl": "https://be54-84-54-90-137.ngrok-free.app/payhistory/success",
        "failUrl": "https://be54-84-54-90-137.ngrok-free.app/payhistory/fail",
        "backUrl": "https://a-b-d.ru/",
        "resultUrl": "https://be54-84-54-90-137.ngrok-free.app/payhistory/callback",
        "expireDate": "",
        "holdMode": "",
        "preference": ""
    }

    # Шаблоны для хешей
    sign_template = "{eshopId}::{orderId}::{serviceName}::{recipientAmount}::{recipientCurrency}::{userName}::{email}::{successUrl}::{failUrl}::{backUrl}::{resultUrl}::{expireDate}::{holdMode}::{preference}::{signSecretKey}"
    hash_template = "{eshopId}::{orderId}::{serviceName}::{recipientAmount}::{recipientCurrency}::{userName}::{email}::{successUrl}::{failUrl}::{backUrl}::{resultUrl}::{expireDate}::{holdMode}::{preference}::{secretKey}"

    # Генерация хешей
    sign_hash = generate_sign_hash(params, sign_template, keys["sign_secret_key"])
    print(sign_hash)
    param_hash = generate_param_hash(params, hash_template, keys["eshop_secret_key"])

    # Запрос к IntellectMoney
    headers = {
        "Authorization": f"Bearer {keys['bearer_token']}",
        "Sign": sign_hash,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    response = requests.post(
        "https://api.intellectmoney.ru/merchant/createInvoice",
        headers=headers,
        data={**params, "hash": param_hash}
    )
    print(response.status_code, response.text)

    if response.status_code == 200:
        data = response.json()
        if data["OperationState"]["Code"] == 0 and data["Result"]["State"]["Code"] == 0:
            invoice_id = data["Result"]["InvoiceId"]
            async with DBApi() as db:
                await db.edit_payhistory(pay_record.id, invoice_id=invoice_id)
            payment_url = f"https://merchant.intellectmoney.ru/init/{invoice_id}/"
            return {
                "message": "Счёт успешно создан",
                "invoice_id": invoice_id,
                "payment_url": payment_url
            }
        raise HTTPException(status_code=400, detail=data["Result"]["State"]["Desc"])
    raise HTTPException(status_code=response.status_code, detail="Ошибка при создании счёта")

# Временные эндпоинты для обработки success и fail
@router.get("/success")
async def payment_success(request: Request):
    """Обработка успешного платежа с перенаправлением на фронтенд."""
    print("SUCCESS")
    print("QUERY PARAMS: ", request.query_params)
    print("PATH PARAMS: ", request.path_params)
    data = await request.json()
    print ("DATA: ", data)
    # async with DBApi() as db:
        # await db.update_payhistory_by_invoice(invoice_id, successfully=True)
        # Здесь можно обновить подписку
    return RedirectResponse(url="https://a-b-d.ru/success")

@router.get("/fail")
async def payment_fail(request: Request):
    """Обработка неуспешного платежа с перенаправлением на фронтенд."""
    print("SUCCESS")
    print("QUERY PARAMS: ", request.query_params)
    print("PATH PARAMS: ", request.path_params)
    data = await request.json()
    print ("DATA: ", data)
    # Можно логировать неудачу, но не обновляем статус
    return RedirectResponse(url="https://a-b-d.ru/fail")

@router.get("/check/{invoice_id}")
async def check_payment_status(invoice_id: int):
    """Проверка статуса платежа через IntellectMoney."""
    async with DBApi() as db:
        # Получаем ключи IntellectMoney
        keys = await get_intellectmoney_keys(db)

    # Параметры для IntellectMoney
    params = {
        "eshopId": keys["eshop_id"],
        "invoiceId": str(invoice_id)
    }

    # Шаблоны для хешей
    sign_template = "{eshopId}::{invoiceId}::{signSecretKey}"
    hash_template = "{eshopId}::{invoiceId}::{secretKey}"

    # Генерация хешей
    sign_hash = generate_sign_hash(params, sign_template, keys["sign_secret_key"])
    param_hash = generate_param_hash(params, hash_template, keys["eshop_secret_key"])

    # Запрос к IntellectMoney
    headers = {
        "Authorization": f"Bearer {keys['bearer_token']}",
        "Sign": sign_hash,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    response = requests.post(
        "https://api.intellectmoney.ru/merchant/getbankcardpaymentstate",
        headers=headers,
        data={**params, "hash": param_hash}
    )

    if response.status_code == 200:
        data = response.json()
        if data["OperationState"]["Code"] == 0 and data["Result"]["State"]["Code"] == 0:
            payment_step = data["Result"]["PaymentStep"]
            async with DBApi() as db:
                if payment_step == "Ok":
                    await db.update_payhistory_by_invoice(invoice_id, successfully=True)
                    # Здесь можно обновить подписку, например:
                    # pay_record = await db.get_payhistory_by_invoice(invoice_id)
                    # await db.update_subscription(pay_record.user_id, pay_record.tariff_id)
                return {"status": payment_step}
        raise HTTPException(status_code=400, detail=data["Result"]["State"]["Desc"])
    raise HTTPException(status_code=response.status_code, detail="Ошибка при проверке статуса")