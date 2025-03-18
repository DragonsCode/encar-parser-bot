from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import telegram_auth, admin_auth
from api.models import SubscriptionCreate, SubscriptionEdit, SubscriptionResponse
from database import DBApi

router = APIRouter(prefix="/subscription", tags=["Subscriptions"])

@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(sub_data: SubscriptionCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        sub = await db.create_subscription(**sub_data.model_dump())
        return await db.get_subscription_by_id(sub.id)  # Предполагается метод с полной информацией

@router.get("/{user_id}", response_model=SubscriptionResponse)
async def get_subscription(user_id: int, auth_user_id: int = Depends(telegram_auth)):
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    async with DBApi() as db:
        sub = await db.get_subscription_by_user(user_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return sub

@router.post("/edit", response_model=SubscriptionResponse)
async def edit_subscription(sub_data: SubscriptionEdit, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        sub = await db.edit_subscription(**sub_data.dict(exclude_unset=True))  # Предполагается метод
        if not sub:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return sub

@router.delete("/{id}")
async def delete_subscription(id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_subscription(id)  # Предполагается метод
        if not success:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return {"success": True}