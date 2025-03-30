import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from datetime import timedelta, datetime
from api.dependencies import telegram_auth
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from api.models import PayHistoryCreate
from database import DBApi
from yookassa import Payment, Configuration

router = APIRouter(prefix="/payhistory", tags=["PayHistory"])

# Модель входных данных для создания платежа
class PaymentCreate(BaseModel):
    tariff_id: int
    email: str
    description: str = "Оплата подписки"

async def get_yookassa_keys(db: DBApi):
    keys = {}
    keys["shop_id"] = (await db.get_setting_by_key("yookassa_shop_id")).value
    keys["shop_secret_key"] = (await db.get_setting_by_key("yookassa_shop_secret_key")).value
    return keys

# Эндпоинт для создания платежа через Юкассу
@router.post("/create")
async def create_payment(payment: PaymentCreate, user_id: int = Depends(telegram_auth)):
    """
    Создаёт запись в истории платежей и инициирует платёж через Юкассу.
    """
    # Создаём запись в истории платежей
    async with DBApi() as db:
        tariff = await db.get_tariff_by_id(payment.tariff_id)
        if not tariff:
            raise HTTPException(status_code=404, detail="Тариф не найден")

    pay_data = PayHistoryCreate(
        user_id=user_id,
        tariff_id=payment.tariff_id,
        price=tariff.price,
        successfully=False
    )
    async with DBApi() as db:
        success = await db.create_pay_history(**pay_data.model_dump())
        if not success:
            raise HTTPException(status_code=400, detail="Ошибка создания записи оплаты")
        # Получаем запись платежа
        pay_record = await db.get_last_payhistory_by_user(user_id)
        # Получаем ключи Юкассы (аналог get_intellectmoney_keys)
        keys = await get_yookassa_keys(db)

    # Настраиваем конфигурацию Юкассы
    Configuration.account_id = keys["shop_id"]
    Configuration.secret_key = keys["shop_secret_key"]

    # Создаём платёж через Юкассу
    try:
        payment_obj = Payment.create({
            "amount": {
                "value": f"{tariff.price:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://a-b-d.ru/success"  # URL возврата после оплаты
            },
            "capture": True,
            "description": payment.description,
            "metadata": {
                "pay_record_id": pay_record.id  # сохраняем ID записи для сопоставления
            }
        }, uuid.uuid4())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка создания платежа: {e}")

    # Обновляем запись с идентификатором платежа (invoice_id)
    async with DBApi() as db:
        await db.edit_payhistory(pay_record.id, invoice_id=payment_obj.id)

    return {
        "message": "Счёт успешно создан",
        "invoice_id": payment_obj.id,
        "payment_url": payment_obj.confirmation.confirmation_url
    }

# Эндпоинт для обработки уведомлений (webhook) от Юкассы
@router.post("/callback")
async def payment_callback(request: Request):
    """
    Обрабатывает уведомления от Юкассы через Webhook.
    Здесь обрабатываются статусы, например, 'payment.succeeded' или 'payment.canceled'.
    """
    event = await request.json()
    event_type = event.get("event")
    payment_obj = event.get("object", {})
    # Из metadata получаем наш внутренний идентификатор записи
    pay_record_id = payment_obj.get("metadata", {}).get("pay_record_id")

    # Здесь можно добавить проверку HTTP-заголовков (например, Basic Auth) для валидации запроса
    if not pay_record_id:
        raise HTTPException(status_code=400, detail="Отсутствует pay_record_id в metadata")

    async with DBApi() as db:
        if event_type == "payment.succeeded":
            payhistory = await db.get_payhistory_by_invoice(payment_obj.get("id"))
            if not payhistory:
                raise HTTPException(status_code=404, detail="Платеж не найден")
            
            if payhistory.successfully:
                return {"status": "ok"}
            
            await db.update_payhistory_by_invoice(payment_obj.get("id"), successfully=True)
            tariff = await db.get_tariff_by_id(payhistory.tariff_id)
            end = datetime.now() + timedelta(days=tariff.days_count)
            await db.create_subscription(payhistory.user_id, payhistory.tariff_id, subscription_end=end)
        elif event_type in ["payment.canceled", "payment.failed"]:
            # Можно залогировать неуспешный платёж или обновить статус записи
            pass

    return {"status": "ok"}

# Эндпоинты для редиректа после успешного/неуспешного платежа
@router.get("/success")
async def payment_success(request: Request):
    """
    Перенаправляет пользователя на фронтенд после успешного платежа.
    """
    return RedirectResponse(url="https://a-b-d.ru/success")

@router.get("/fail")
async def payment_fail(request: Request):
    """
    Перенаправляет пользователя на фронтенд после неуспешного платежа.
    """
    return RedirectResponse(url="https://a-b-d.ru/fail")

@router.get("/last")
async def get_last_pay_history(user_id: int = Depends(telegram_auth)):
    async with DBApi() as db:
        pay_history = await db.get_last_payhistory_by_user(user_id)
        if not pay_history:
            raise HTTPException(status_code=404, detail="Запись в истории платежей не найдена")
        return pay_history

# Эндпоинт для проверки статуса платежа через Юкассу
@router.get("/check/{invoice_id}")
async def check_payment_status(invoice_id: str, user_id: int = Depends(telegram_auth)):
    """
    Позволяет проверить статус платежа по invoice_id.
    """
    async with DBApi() as db:
        # Получаем запись платежа
        pay_record = await db.get_payhistory_by_invoice(invoice_id)
    
    if not pay_record:
        raise HTTPException(status_code=404, detail="Запись в истории платежей не найдена")
    
    if pay_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для проверки статуса платежа")
        
    # Получаем ключи Юкассы
    async with DBApi() as db:
        keys = await get_yookassa_keys(db)
    Configuration.account_id = keys["shop_id"]
    Configuration.secret_key = keys["shop_secret_key"]

    try:
        payment_obj = Payment.find_one(invoice_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка проверки платежа: {e}")

    # Обновляем статус записи, если платёж успешен
    if payment_obj.status == "succeeded":
        payhistory = await db.get_payhistory_by_invoice(invoice_id)
        if not payhistory:
            raise HTTPException(status_code=404, detail="Платеж не найден")
        
        if payhistory.successfully:
            return {"status": "ok"}
        
        await db.update_payhistory_by_invoice(invoice_id, successfully=True)
        tariff = await db.get_tariff_by_id(payhistory.tariff_id)
        end = datetime.now() + timedelta(days=tariff.days_count)
        await db.create_subscription(payhistory.user_id, payhistory.tariff_id, subscription_end=end)
    return {"status": payment_obj.status}
