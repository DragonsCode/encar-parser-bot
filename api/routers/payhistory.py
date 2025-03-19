from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import admin_auth
from api.models import PayHistoryCreate, PayHistoryEdit
from database import DBApi

router = APIRouter(prefix="/payhistory", tags=["PayHistory"])

@router.post("/create")
async def create_payhistory(pay_data: PayHistoryCreate, is_admin: bool = Depends(admin_auth)):
    """
    Depends on admin_auth
    """
    async with DBApi() as db:
        success = await db.create_payhistory(**pay_data.model_dump())  # Предполагается метод
        if not success:
            raise HTTPException(status_code=400, detail="Ошибка создания записи оплаты")
        return {"success": True}

@router.post("/edit")
async def edit_payhistory(pay_data: PayHistoryEdit, is_admin: bool = Depends(admin_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        success = await db.edit_payhistory(**pay_data.model_dump(exclude_unset=True))  # Предполагается метод
        if not success:
            raise HTTPException(status_code=404, detail="Запись оплаты не найдена")
        return {"success": True}