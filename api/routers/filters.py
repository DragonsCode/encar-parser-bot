from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import telegram_auth, admin_auth
from api.models import FilterCreate, FilterResponse
from database import DBApi
from typing import List

router = APIRouter(prefix="/filter", tags=["Filters"])

@router.post("/create", response_model=FilterResponse)
async def create_filter(filter_data: FilterCreate, user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        # Проверка лимита фильтров (по подписке)
        subscription = await db.get_subscription_by_user(user_id)
        if not subscription:
            raise HTTPException(status_code=403, detail="У вас нет активной подписки")
        
        tariff = await db.get_tariff_by_id(subscription.tariff_id)  # Предполагается метод
        filters_count = await db.get_filters_count_by_user(user_id)  # Предполагается метод
        if filters_count >= tariff.filter_count:
            raise HTTPException(status_code=403, detail="Превышен лимит фильтров. Удалите старые или обновите подписку")
        
        # Создание фильтра
        filter_obj = await db.create_filter(**filter_data.model_dump())  # Предполагается метод
        return await db.get_filter_by_id(filter_obj.id)  # Предполагается метод с полной информацией

@router.get("/{user_id}", response_model=List[FilterResponse])
async def get_filters(user_id: int, auth_user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    async with DBApi() as db:
        filters = await db.get_filters_by_user(user_id)  # Предполагается метод
        return filters

@router.delete("/{id}")
async def delete_filter(id: int, is_admin: bool = Depends(admin_auth)):
    """
    Depends on admin_auth
    """
    async with DBApi() as db:
        success = await db.delete_filter(id)  # Предполагается метод
        if not success:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        return {"success": True}