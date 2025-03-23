from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import DBApi

router = APIRouter(prefix="/admin/car", tags=["Admin - Car"])

# Модель для создания записи
class CarCreate(BaseModel):
    manufacture_id: int
    model_id: int
    series_id: int
    equipment_id: int
    engine_type_id: int
    car_color_id: int
    mileage: Optional[int] = None
    price_won: Optional[int] = None
    price_rub: Optional[int] = None
    date_release: Optional[datetime] = None
    publication_dttm: Optional[datetime] = None
    check_dttm: Optional[datetime] = None
    change_ownership: Optional[int] = None
    all_traffic_accident: Optional[int] = None
    traffic_accident_owner: Optional[int] = None
    traffic_accident_other: Optional[int] = None
    repair_cost_owner: Optional[float] = None
    repair_cost_other: Optional[float] = None
    theft: Optional[int] = None
    flood: Optional[int] = None
    death: Optional[int] = None
    url: Optional[str] = None

# Модель для обновления записи
class CarUpdate(BaseModel):
    manufacture_id: Optional[int] = None
    model_id: Optional[int] = None
    series_id: Optional[int] = None
    equipment_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    car_color_id: Optional[int] = None
    mileage: Optional[int] = None
    price_won: Optional[int] = None
    price_rub: Optional[int] = None
    date_release: Optional[datetime] = None
    publication_dttm: Optional[datetime] = None
    check_dttm: Optional[datetime] = None
    change_ownership: Optional[int] = None
    all_traffic_accident: Optional[int] = None
    traffic_accident_owner: Optional[int] = None
    traffic_accident_other: Optional[int] = None
    repair_cost_owner: Optional[float] = None
    repair_cost_other: Optional[float] = None
    theft: Optional[int] = None
    flood: Optional[int] = None
    death: Optional[int] = None
    url: Optional[str] = None

# Модель для ответа
class CarResponse(BaseModel):
    id: int
    manufacture_id: int
    model_id: int
    series_id: int
    equipment_id: int
    engine_type_id: int
    car_color_id: int
    mileage: Optional[int] = None
    price_won: Optional[int] = None
    price_rub: Optional[int] = None
    date_release: Optional[datetime] = None
    publication_dttm: Optional[datetime] = None
    check_dttm: Optional[datetime] = None
    change_ownership: Optional[int] = None
    all_traffic_accident: Optional[int] = None
    traffic_accident_owner: Optional[int] = None
    traffic_accident_other: Optional[int] = None
    repair_cost_owner: Optional[float] = None
    repair_cost_other: Optional[float] = None
    theft: Optional[int] = None
    flood: Optional[int] = None
    death: Optional[int] = None
    url: Optional[str] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание автомобиля
@router.post("/", response_model=CarResponse, status_code=status.HTTP_201_CREATED)
async def create_car(car: CarCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        car_data = await db.create_car(**car.dict())
        if not car_data:
            raise HTTPException(status_code=400, detail="Ошибка при создании автомобиля")
        return car_data

# Получение всех автомобилей
@router.get("/", response_model=List[CarResponse])
async def get_all_cars(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        car_ids = await db.get_all_cars()
        return car_ids

# Получение автомобиля по ID
@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        car = await db.get_car_by_id(car_id)
        if not car:
            raise HTTPException(status_code=404, detail="Автомобиль не найден")
        return car

# Обновление автомобиля
@router.put("/{car_id}", response_model=CarResponse)
async def update_car(car_id: int, car: CarUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_car = await db.update_car(car_id, **car.dict(exclude_unset=True))
        if not updated_car:
            raise HTTPException(status_code=404, detail="Автомобиль не найден")
        return updated_car

# Удаление автомобиля
@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(car_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_car(car_id)
        if not success:
            raise HTTPException(status_code=404, detail="Автомобиль не найден")
        return None