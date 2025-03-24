from fastapi import APIRouter, Depends
from api.dependencies import telegram_auth
from api.models import TariffResponse
from database import DBApi
from typing import List

router = APIRouter(prefix="/tariffs", tags=["Tariffs"])

@router.get("/", response_model=List[TariffResponse])
async def get_tariffs(user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        tariffs = await db.get_all_tariffs()
        return tariffs