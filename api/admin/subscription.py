from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import DBApi
from fastapi_pagination import Page  # Импортируем Page для пагинации
from fastapi_pagination.ext.sqlalchemy import paginate  # Импортируем paginate для SQLAlchemy

router = APIRouter(prefix="/admin/subscription", tags=["Admin - Subscription"])

# Модель для создания записи
class SubscriptionCreate(BaseModel):
    user_id: int
    tariff_id: int
    subscription_end: datetime

# Модель для обновления записи
class SubscriptionUpdate(BaseModel):
    user_id: Optional[int] = None
    tariff_id: Optional[int] = None
    subscription_end: Optional[datetime] = None

# Модель для ответа
class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    tariff_id: int
    subscription_end: Optional[datetime] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание подписки
@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(subscription: SubscriptionCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        subscription_data = await db.create_subscription(
            user_id=subscription.user_id,
            tariff_id=subscription.tariff_id,
            subscription_end=subscription.subscription_end
        )
        if not subscription_data:
            raise HTTPException(status_code=400, detail="Ошибка при создании подписки")
        return subscription_data

# Получение всех подписок с пагинацией
@router.get("/", response_model=Page[SubscriptionResponse])
async def get_all_subscriptions(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        # Используем новый метод get_all_subscriptions_query для получения SQLAlchemy-запроса
        query = await db.get_all_subscriptions_query()
        return await paginate(db._sess, query)

# Получение подписки по пользователю
@router.get("/user/{user_id}", response_model=Page[SubscriptionResponse])
async def get_subscription_by_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        subscription = await db.get_subscription_by_user_query(user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return paginate(db._sess, subscription)

# Получение подписок, истекающих в заданном временном интервале, с пагинацией
@router.get("/expiring", response_model=Page[SubscriptionResponse])
async def get_expiring_subscriptions(start_time: datetime, end_time: datetime, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        # Используем новый метод get_expiring_subscriptions_query для получения SQLAlchemy-запроса
        query = await db.get_expiring_subscriptions_query(start_time, end_time)
        return await paginate(db._sess, query)

# Получение подписки по ID
@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        subscription = await db.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return subscription

# Обновление подписки
@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(subscription_id: int, subscription: SubscriptionUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_subscription = await db.update_subscription(subscription_id, **subscription.dict(exclude_unset=True))
        if not updated_subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return updated_subscription

# Удаление подписки
@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_subscription(subscription_id)
        if not success:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return None