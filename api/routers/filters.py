from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import telegram_auth, admin_auth
from api.models import FilterCreate, FilterResponse
from database import DBApi
from typing import List
from functions.new_filter import send_car_by_filter

router = APIRouter(prefix="/filter", tags=["Filters"])

@router.post("/create", response_model=FilterResponse)
async def create_filter(filter_data: FilterCreate, user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        # Проверка лимита фильтров (по подписке)
        subscription = await db.get_active_subscription_by_user(user_id)
        if not subscription:
            raise HTTPException(status_code=403, detail="У вас нет активной подписки")
        
        tariff = await db.get_tariff_by_id(subscription.tariff_id)
        filters_count = await db.get_filters_count_by_user(user_id)
        if filters_count >= tariff.filters_count:
            raise HTTPException(status_code=403, detail="Превышен лимит фильтров. Удалите старые или обновите подписку")
        
        # Создание фильтра
        filter_obj = await db.create_filter(user_id, **filter_data.model_dump())
        filter_fetched = await db.get_filter_by_id(filter_obj.id)
        if not filter_fetched:
            raise HTTPException(status_code=404, detail="Фильтр не найден после создания")
        await send_car_by_filter(user_id, filter_obj.id)
        return FilterResponse.model_validate(filter_fetched)

@router.get("/{user_id}", response_model=List[FilterResponse])
async def get_filters(auth_user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        filters = await db.get_filters_by_user(auth_user_id)
        return [FilterResponse.model_validate(f) for f in filters]

@router.delete("/{id}")
async def delete_filter(id: int, is_admin: bool = Depends(admin_auth)):
    """
    Depends on admin_auth
    """
    async with DBApi() as db:
        success = await db.delete_filter(id)
        if not success:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        return {"success": True}