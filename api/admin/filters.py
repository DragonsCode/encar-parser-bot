from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import DBApi

router = APIRouter(prefix="/admin/filters", tags=["Admin - Filters"])

# Модель для создания записи
class FilterCreate(BaseModel):
    user_id: int
    manufacture_id: Optional[int] = None
    model_id: Optional[int] = None
    series_id: Optional[int] = None
    equipment_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    drive_type_id: Optional[int] = None
    car_color_id: Optional[int] = None
    mileage_from: Optional[int] = None
    mileage_defore: Optional[int] = None
    price_from: Optional[int] = None
    price_defore: Optional[int] = None
    date_release_from: Optional[datetime] = None
    date_release_defore: Optional[datetime] = None

# Модель для обновления записи
class FilterUpdate(BaseModel):
    user_id: Optional[int] = None
    manufacture_id: Optional[int] = None
    model_id: Optional[int] = None
    series_id: Optional[int] = None
    equipment_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    drive_type_id: Optional[int] = None
    car_color_id: Optional[int] = None
    mileage_from: Optional[int] = None
    mileage_defore: Optional[int] = None
    price_from: Optional[int] = None
    price_defore: Optional[int] = None
    date_release_from: Optional[datetime] = None
    date_release_defore: Optional[datetime] = None

# Модель для ответа
class FilterResponse(BaseModel):
    id: int
    user_id: int
    manufacture_id: Optional[int] = None
    model_id: Optional[int] = None
    series_id: Optional[int] = None
    equipment_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    drive_type_id: Optional[int] = None
    car_color_id: Optional[int] = None
    mileage_from: Optional[int] = None
    mileage_defore: Optional[int] = None
    price_from: Optional[int] = None
    price_defore: Optional[int] = None
    date_release_from: Optional[datetime] = None
    date_release_defore: Optional[datetime] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание фильтра
@router.post("/", response_model=FilterResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(filter_data: FilterCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        filter_obj = await db.create_filter(
            user_id=filter_data.user_id,
            manufacture_id=filter_data.manufacture_id,
            model_id=filter_data.model_id,
            series_id=filter_data.series_id,
            equipment_id=filter_data.equipment_id,
            engine_type_id=filter_data.engine_type_id,
            drive_type_id=filter_data.drive_type_id,
            car_color_id=filter_data.car_color_id,
            mileage_from=filter_data.mileage_from,
            mileage_defore=filter_data.mileage_defore,
            price_from=filter_data.price_from,
            price_defore=filter_data.price_defore,
            date_release_from=filter_data.date_release_from,
            date_release_defore=filter_data.date_release_defore
        )
        if not filter_obj:
            raise HTTPException(status_code=400, detail="Ошибка при создании фильтра")
        return filter_obj

# Получение всех фильтров
@router.get("/", response_model=List[FilterResponse])
async def get_all_filters(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        filters = await db.get_all_filters()
        return filters

# Получение фильтров по пользователю
@router.get("/user/{user_id}", response_model=List[FilterResponse])
async def get_filters_by_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        filters = await db.get_filters_by_user(user_id)
        return filters

# Получение количества фильтров пользователя
@router.get("/count/{user_id}", response_model=int)
async def get_filters_count_by_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        count = await db.get_filters_count_by_user(user_id)
        return count

# Получение фильтра по ID
@router.get("/{filter_id}", response_model=FilterResponse)
async def get_filter(filter_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        filter_obj = await db.get_filter_by_id(filter_id)
        if not filter_obj:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        return filter_obj

# Обновление фильтра
@router.put("/{filter_id}", response_model=FilterResponse)
async def update_filter(filter_id: int, filter_data: FilterUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_filter = await db.update_filter(filter_id, **filter_data.dict(exclude_unset=True))
        if not updated_filter:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        return updated_filter

# Удаление фильтра
@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(filter_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_filter(filter_id)
        if not success:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        return None