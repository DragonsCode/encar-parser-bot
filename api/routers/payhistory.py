from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from api.dependencies import admin_auth
from api.models import PayHistoryCreate
from api.utils.intellectmoney import get_intellectmoney_keys, generate_sign_hash, generate_param_hash
from database import DBApi
import requests

router = APIRouter(prefix="/payhistory", tags=["PayHistory"])

class PaymentCreate(BaseModel):
    user_id: int
    tariff_id: int
    price: int
    email: str
    description: str = "Оплата подписки"

@router.post("/callback")
async def payment_callback(request: Request):
    """Обработка уведомлений от IntellectMoney."""
    data = await request.json()
    print("CALLBACK DATA: ", data)
    invoice_id = data.get("invoiceId")
    payment_step = data.get("paymentStep")

    if not invoice_id or not payment_step:
        raise HTTPException(status_code=400, detail="Отсутствуют обязательные параметры invoiceId или paymentStep")

    async with DBApi() as db:
        if payment_step == "Ok":
            await db.update_payhistory_by_invoice(invoice_id, successfully=True)
            # Здесь можно обновить подписку, например:
            # pay_record = await db.get_payhistory_by_invoice(invoice_id)
            # await db.update_subscription(pay_record.user_id, pay_record.tariff_id)
        elif payment_step == "Error":
            # Можно логировать неудачу, но не обновляем статус
            pass

    return {"message": "Callback обработан"}

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
        "successUrl": "http://localhost:8000/payhistory/success",
        "failUrl": "http://localhost:8000/payhistory/fail",
        "backUrl": "https://a-b-d.ru/",
        "resultUrl": "http://localhost:8000/payhistory/callback",
        "expireDate": "",
        "holdMode": "",
        "preference": ""
    }

    # Шаблоны для хешей
    sign_template = "{eshopId}::{orderId}::{serviceName}::{recipientAmount}::{recipientCurrency}::{userName}::{email}::{successUrl}::{failUrl}::{backUrl}::{resultUrl}::{expireDate}::{holdMode}::{preference}::{signSecretKey}"
    hash_template = "{eshopId}::{orderId}::{serviceName}::{recipientAmount}::{recipientCurrency}::{userName}::{email}::{successUrl}::{failUrl}::{backUrl}::{resultUrl}::{expireDate}::{holdMode}::{preference}::{secretKey}"

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
        "https://api.intellectmoney.ru/merchant/createInvoice",
        headers=headers,
        data={**params, "hash": param_hash}
    )

    if response.status_code == 200:
        data = response.json()
        if data["OperationState"]["Code"] == 0 and data["Result"]["State"]["Code"] == 0:
            invoice_id = data["Result"]["InvoiceId"]
            async with DBApi() as db:
                await db.edit_payhistory(pay_record.id, intellect_invoice_id=invoice_id)
            payment_url = f"https://merchant.intellectmoney.ru/v2/ru/process/{invoice_id}/acquiring"
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