from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import DBApi
from fastapi_pagination import Page  # Импортируем Page для пагинации
from fastapi_pagination.ext.sqlalchemy import paginate  # Импортируем paginate для SQLAlchemy

router = APIRouter(prefix="/admin/tariffs", tags=["Admin - Tariffs"])

# Модель для создания записи
class TariffCreate(BaseModel):
    name: str
    description: str
    days_count: int
    price: float
    filters_count: int

# Модель для обновления записи
class TariffUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    days_count: Optional[int] = None
    price: Optional[float] = None
    filters_count: Optional[int] = None

# Модель для ответа
class TariffResponse(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    days_count: Optional[int] = None
    price: Optional[float] = None
    filters_count: Optional[int] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание тарифа
@router.post("/", response_model=TariffResponse, status_code=status.HTTP_201_CREATED)
async def create_tariff(tariff: TariffCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        tariff_data = await db.create_tariff(
            name=tariff.name,
            description=tariff.description,
            days_count=tariff.days_count,
            price=tariff.price,
            filters_count=tariff.filters_count
        )
        if not tariff_data:
            raise HTTPException(status_code=400, detail="Ошибка при создании тарифа")
        return tariff_data

# Получение всех тарифов с пагинацией
@router.get("/", response_model=Page[TariffResponse])
async def get_all_tariffs(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        # Используем новый метод get_all_tariffs_query для получения SQLAlchemy-запроса
        query = await db.get_all_tariffs_query()
        return await paginate(db._sess, query)

# Получение тарифа по ID
@router.get("/{tariff_id}", response_model=TariffResponse)
async def get_tariff(tariff_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        tariff = await db.get_tariff_by_id(tariff_id)
        if not tariff:
            raise HTTPException(status_code=404, detail="Тариф не найден")
        return tariff

# Обновление тарифа
@router.put("/{tariff_id}", response_model=TariffResponse)
async def update_tariff(tariff_id: int, tariff: TariffUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_tariff = await db.update_tariff(tariff_id, **tariff.dict(exclude_unset=True))
        if not updated_tariff:
            raise HTTPException(status_code=404, detail="Тариф не найден")
        return updated_tariff

# Удаление тарифа
@router.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tariff(tariff_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_tariff(tariff_id)
        if not success:
            raise HTTPException(status_code=404, detail="Тариф не найден")
        return None