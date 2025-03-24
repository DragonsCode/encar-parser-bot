from fastapi import APIRouter, Depends
from api.dependencies import telegram_auth
from api.models import ReferenceResponse
from database import DBApi
from typing import List

router = APIRouter(prefix="/references", tags=["References"])

@router.get("/manufactury", response_model=List[ReferenceResponse])
async def get_manufacturers(user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        return await db.get_all_manufactures()

@router.get("/model/{manufactury_id}", response_model=List[ReferenceResponse])
async def get_models(manufactury_id: int, user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        return await db.get_models_by_manufacture(manufactury_id)

@router.get("/series/{model_id}", response_model=List[ReferenceResponse])
async def get_series(model_id: int, user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        return await db.get_series_by_model(model_id)

@router.get("/equipment/{series_id}", response_model=List[ReferenceResponse])
async def get_equipment(series_id: int, user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        return await db.get_equipment_by_series(series_id)

@router.get("/engineType", response_model=List[ReferenceResponse])
async def get_engine_types(user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        return await db.get_all_engine_types()

@router.get("/driveType", response_model=List[ReferenceResponse])
async def get_drive_types(user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        return await db.get_all_drive_types()

@router.get("/carColor", response_model=List[ReferenceResponse])
async def get_car_colors(user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        return await db.get_all_car_colors()