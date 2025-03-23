from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import DBApi

router = APIRouter(prefix="/admin/payhistory", tags=["Admin - PayHistory"])

# Модель для создания записи
class PayHistoryCreate(BaseModel):
    user_id: int
    tariff_id: int
    price: Optional[float] = None
    successfully: Optional[bool] = None
    intellect_invoice_id: Optional[int] = None

# Модель для обновления записи
class PayHistoryUpdate(BaseModel):
    user_id: Optional[int] = None
    tariff_id: Optional[int] = None
    price: Optional[float] = None
    successfully: Optional[bool] = None
    intellect_invoice_id: Optional[int] = None

# Модель для ответа
class PayHistoryResponse(BaseModel):
    id: int
    user_id: int
    tariff_id: int
    price: Optional[float] = None
    successfully: Optional[bool] = None
    intellect_invoice_id: Optional[int] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание записи в истории платежей
@router.post("/", response_model=PayHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_pay_history(pay_history: PayHistoryCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        pay_history_data = await db.create_pay_history(
            user_id=pay_history.user_id,
            tariff_id=pay_history.tariff_id,
            price=pay_history.price,
            successfully=pay_history.successfully,
            intellect_invoice_id=pay_history.intellect_invoice_id
        )
        if not pay_history_data:
            raise HTTPException(status_code=400, detail="Ошибка при создании записи в истории платежей")
        return pay_history_data

# Получение всех записей в истории платежей
@router.get("/", response_model=List[PayHistoryResponse])
async def get_all_pay_histories(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        pay_histories = await db.get_all_pay_histories()
        return pay_histories

# Получение истории платежей по пользователю
@router.get("/user/{user_id}", response_model=List[PayHistoryResponse])
async def get_pay_history_by_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        pay_histories = await db.get_pay_history_by_user(user_id)
        return pay_histories

# Получение последней записи в истории платежей пользователя
@router.get("/last/{user_id}", response_model=PayHistoryResponse)
async def get_last_pay_history_by_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        pay_history = await db.get_last_payhistory_by_user(user_id)
        if not pay_history:
            raise HTTPException(status_code=404, detail="Запись в истории платежей не найдена")
        return pay_history

# Получение записи в истории платежей по ID
@router.get("/{pay_history_id}", response_model=PayHistoryResponse)
async def get_pay_history(pay_history_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        pay_history = await db.get_pay_history_by_id(pay_history_id)
        if not pay_history:
            raise HTTPException(status_code=404, detail="Запись в истории платежей не найдена")
        return pay_history

# Получение записи в истории платежей по invoice_id
@router.get("/invoice/{invoice_id}", response_model=PayHistoryResponse)
async def get_pay_history_by_invoice(invoice_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        pay_history = await db.get_payhistory_by_invoice(invoice_id)
        if not pay_history:
            raise HTTPException(status_code=404, detail="Запись в истории платежей не найдена")
        return pay_history

# Обновление записи в истории платежей
@router.put("/{pay_history_id}", response_model=PayHistoryResponse)
async def update_pay_history(pay_history_id: int, pay_history: PayHistoryUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_pay_history = await db.update_pay_history(pay_history_id, **pay_history.dict(exclude_unset=True))
        if not updated_pay_history:
            raise HTTPException(status_code=404, detail="Запись в истории платежей не найдена")
        return updated_pay_history

# Удаление записи в истории платежей
@router.delete("/{pay_history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pay_history(pay_history_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_pay_history(pay_history_id)
        if not success:
            raise HTTPException(status_code=404, detail="Запись в истории платежей не найдена")
        return None