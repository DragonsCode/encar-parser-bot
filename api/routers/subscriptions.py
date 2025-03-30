from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import telegram_auth, admin_auth
from api.models import SubscriptionCreate, SubscriptionEdit, SubscriptionResponse, TariffResponse
from database import DBApi
from typing import List

router = APIRouter(prefix="/subscription", tags=["Subscriptions"])

@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(sub_data: SubscriptionCreate, is_admin: bool = Depends(admin_auth)):
    """
    Depends on admin_auth
    """
    async with DBApi() as db:
        sub = await db.create_subscription(**sub_data.model_dump())
        return await db.get_subscription_by_id(sub.id)

@router.get("/", response_model=List[SubscriptionResponse])
async def get_subscription(auth_user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        subs = await db.get_subscription_by_user(auth_user_id)
        if not subs:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        res = []
        for sub in subs:
            tariff = await db.get_tariff_by_id(sub.tariff_id)
            if not tariff:
                raise HTTPException(status_code=404, detail=f"Тариф с ID {sub.tariff_id} не найден")
            res.append(
                SubscriptionResponse(
                id=sub.id,
                user_id=sub.user_id,
                tariff=TariffResponse.model_validate(tariff),
                subscription_end=sub.subscription_end,
                create_dttm=sub.create_dttm,
                update_dttm=sub.update_dttm
            )
            )
        return res

@router.get("/active", response_model=SubscriptionResponse)
async def get_active_subscription(auth_user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        sub = await db.get_active_subscription_by_user(auth_user_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        tariff = await db.get_tariff_by_id(sub.tariff_id)
        if not tariff:
            raise HTTPException(status_code=404, detail=f"Тариф с ID {sub.tariff_id} не найден")
        return SubscriptionResponse(
            id=sub.id,
            user_id=sub.user_id,
            tariff=TariffResponse.model_validate(tariff),
            subscription_end=sub.subscription_end,
            create_dttm=sub.create_dttm,
            update_dttm=sub.update_dttm
        )

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