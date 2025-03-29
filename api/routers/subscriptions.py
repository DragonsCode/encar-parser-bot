from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import telegram_auth, admin_auth
from api.models import SubscriptionCreate, SubscriptionEdit, SubscriptionResponse
from database import DBApi

router = APIRouter(prefix="/subscription", tags=["Subscriptions"])

@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(sub_data: SubscriptionCreate, is_admin: bool = Depends(admin_auth)):
    """
    Depends on admin_auth
    """
    async with DBApi() as db:
        sub = await db.create_subscription(**sub_data.model_dump())
        return await db.get_subscription_by_id(sub.id)

@router.get("/{user_id}", response_model=SubscriptionResponse)
async def get_subscription(user_id: int, auth_user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        sub = await db.get_subscription_by_user(auth_user_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        # Преобразуем объект SQLAlchemy в Pydantic-модель
        return SubscriptionResponse.model_validate(sub)

@router.post("/edit", response_model=SubscriptionResponse)
async def edit_subscription(sub_data: SubscriptionEdit, is_admin: bool = Depends(admin_auth)):
    """
    Depends on admin_auth
    """
    async with DBApi() as db:
        sub = await db.edit_subscription(**sub_data.model_dump(exclude_unset=True))
        if not sub:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return sub

@router.delete("/{id}")
async def delete_subscription(id: int, is_admin: bool = Depends(admin_auth)):
    """
    Depends on admin_auth
    """
    async with DBApi() as db:
        success = await db.delete_subscription(id)
        if not success:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return {"success": True}