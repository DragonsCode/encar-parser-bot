from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import DBApi
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter(prefix="/admin/filters", tags=["Admin - Filters"])

# Модель для создания записи
class FilterCreate(BaseModel):
    user_id: int
    manufacture_id: Optional[int] = None
    model_id: Optional[int] = None
    series_id: Optional[int] = None
    equipment_ids: List[int] = []  # Список ID комплектаций
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
    equipment_ids: Optional[List[int]] = None  # Список ID комплектаций (опционально)
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
    manufacture: Optional[str] = None
    model: Optional[str] = None
    series: Optional[str] = None
    equipment: List[str] = []  # Список переводов комплектаций
    engine_type: Optional[str] = None
    drive_type_id: Optional[int] = None
    car_color: Optional[str] = None
    mileage_from: Optional[int] = None
    mileage_defore: Optional[int] = None
    price_from: Optional[int] = None
    price_defore: Optional[int] = None
    date_release_from: Optional[datetime] = None
    date_release_defore: Optional[datetime] = None
    create_dttm: datetime
    update_dttm: datetime

    class Config:
        from_attributes = True

# Создание фильтра
@router.post("/", response_model=FilterResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(filter_data: FilterCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        # Создание фильтра без equipment_ids
        filter_obj = await db.create_filter(
            user_id=filter_data.user_id,
            manufacture_id=filter_data.manufacture_id,
            model_id=filter_data.model_id,
            series_id=filter_data.series_id,
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
        # Добавление комплектаций
        for equipment_id in filter_data.equipment_ids:
            await db.add_equipment_to_filter(filter_obj.id, equipment_id)
        
        # Формирование ответа с переводами
        manufacture = await db.get_manufacture_by_id(filter_obj.manufacture_id) if filter_obj.manufacture_id else None
        model = await db.get_model_by_id(filter_obj.model_id) if filter_obj.model_id else None
        series = await db.get_series_by_id(filter_obj.series_id) if filter_obj.series_id else None
        equipment_ids = await db.get_equipment_ids_by_filter(filter_obj.id)
        equipments = [await db.get_equipment_by_id(eid) for eid in equipment_ids]
        engine_type = await db.get_engine_type_by_id(filter_obj.engine_type_id) if filter_obj.engine_type_id else None
        car_color = await db.get_car_color_by_id(filter_obj.car_color_id) if filter_obj.car_color_id else None

        response_data = {
            "id": filter_obj.id,
            "user_id": filter_obj.user_id,
            "manufacture": manufacture.translated if manufacture else None,
            "model": model.translated if model else None,
            "series": series.translated if series else None,
            "equipment": [eq.translated for eq in equipments if eq],
            "engine_type": engine_type.translated if engine_type else None,
            "drive_type_id": filter_obj.drive_type_id,
            "car_color": car_color.translated if car_color else None,
            "mileage_from": filter_obj.mileage_from,
            "mileage_defore": filter_obj.mileage_defore,
            "price_from": filter_obj.price_from,
            "price_defore": filter_obj.price_defore,
            "date_release_from": filter_obj.date_release_from,
            "date_release_defore": filter_obj.date_release_defore,
            "create_dttm": filter_obj.create_dttm,
            "update_dttm": filter_obj.update_dttm
        }
        return FilterResponse(**response_data)

# Получение всех фильтров с пагинацией
@router.get("/", response_model=Page[FilterResponse])
async def get_all_filters(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        query = await db.get_all_filters_query()
        filters = await db._sess.execute(query).scalars().all()
        filters_data = []
        for filter_obj in filters:
            manufacture = await db.get_manufacture_by_id(filter_obj.manufacture_id) if filter_obj.manufacture_id else None
            model = await db.get_model_by_id(filter_obj.model_id) if filter_obj.model_id else None
            series = await db.get_series_by_id(filter_obj.series_id) if filter_obj.series_id else None
            equipment_ids = await db.get_equipment_ids_by_filter(filter_obj.id)
            equipments = [await db.get_equipment_by_id(eid) for eid in equipment_ids]
            engine_type = await db.get_engine_type_by_id(filter_obj.engine_type_id) if filter_obj.engine_type_id else None
            car_color = await db.get_car_color_by_id(filter_obj.car_color_id) if filter_obj.car_color_id else None

            filters_data.append(
                {
                    "id": filter_obj.id,
                    "user_id": filter_obj.user_id,
                    "manufacture": manufacture.translated if manufacture else None,
                    "model": model.translated if model else None,
                    "series": series.translated if series else None,
                    "equipment": [eq.translated for eq in equipments if eq],
                    "engine_type": engine_type.translated if engine_type else None,
                    "drive_type_id": filter_obj.drive_type_id,
                    "car_color": car_color.translated if car_color else None,
                    "mileage_from": filter_obj.mileage_from,
                    "mileage_defore": filter_obj.mileage_defore,
                    "price_from": filter_obj.price_from,
                    "price_defore": filter_obj.price_defore,
                    "date_release_from": filter_obj.date_release_from,
                    "date_release_defore": filter_obj.date_release_defore,
                    "create_dttm": filter_obj.create_dttm,
                    "update_dttm": filter_obj.update_dttm
                }
            )
        return await paginate(db._sess, query, response_type=List[FilterResponse], response_data=[FilterResponse(**f) for f in filters_data])

# Получение фильтров по пользователю с пагинацией
@router.get("/user/{user_id}", response_model=Page[FilterResponse])
async def get_filters_by_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        query = await db.get_filters_by_user_query(user_id)
        filters = await db._sess.execute(query).scalars().all()
        filters_data = []
        for filter_obj in filters:
            manufacture = await db.get_manufacture_by_id(filter_obj.manufacture_id) if filter_obj.manufacture_id else None
            model = await db.get_model_by_id(filter_obj.model_id) if filter_obj.model_id else None
            series = await db.get_series_by_id(filter_obj.series_id) if filter_obj.series_id else None
            equipment_ids = await db.get_equipment_ids_by_filter(filter_obj.id)
            equipments = [await db.get_equipment_by_id(eid) for eid in equipment_ids]
            engine_type = await db.get_engine_type_by_id(filter_obj.engine_type_id) if filter_obj.engine_type_id else None
            car_color = await db.get_car_color_by_id(filter_obj.car_color_id) if filter_obj.car_color_id else None

            filters_data.append(
                {
                    "id": filter_obj.id,
                    "user_id": filter_obj.user_id,
                    "manufacture": manufacture.translated if manufacture else None,
                    "model": model.translated if model else None,
                    "series": series.translated if series else None,
                    "equipment": [eq.translated for eq in equipments if eq],
                    "engine_type": engine_type.translated if engine_type else None,
                    "drive_type_id": filter_obj.drive_type_id,
                    "car_color": car_color.translated if car_color else None,
                    "mileage_from": filter_obj.mileage_from,
                    "mileage_defore": filter_obj.mileage_defore,
                    "price_from": filter_obj.price_from,
                    "price_defore": filter_obj.price_defore,
                    "date_release_from": filter_obj.date_release_from,
                    "date_release_defore": filter_obj.date_release_defore,
                    "create_dttm": filter_obj.create_dttm,
                    "update_dttm": filter_obj.update_dttm
                }
            )
        return await paginate(db._sess, query, response_type=List[FilterResponse], response_data=[FilterResponse(**f) for f in filters_data])

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
        
        manufacture = await db.get_manufacture_by_id(filter_obj.manufacture_id) if filter_obj.manufacture_id else None
        model = await db.get_model_by_id(filter_obj.model_id) if filter_obj.model_id else None
        series = await db.get_series_by_id(filter_obj.series_id) if filter_obj.series_id else None
        equipment_ids = await db.get_equipment_ids_by_filter(filter_obj.id)
        equipments = [await db.get_equipment_by_id(eid) for eid in equipment_ids]
        engine_type = await db.get_engine_type_by_id(filter_obj.engine_type_id) if filter_obj.engine_type_id else None
        car_color = await db.get_car_color_by_id(filter_obj.car_color_id) if filter_obj.car_color_id else None

        response_data = {
            "id": filter_obj.id,
            "user_id": filter_obj.user_id,
            "manufacture": manufacture.translated if manufacture else None,
            "model": model.translated if model else None,
            "series": series.translated if series else None,
            "equipment": [eq.translated for eq in equipments if eq],
            "engine_type": engine_type.translated if engine_type else None,
            "drive_type_id": filter_obj.drive_type_id,
            "car_color": car_color.translated if car_color else None,
            "mileage_from": filter_obj.mileage_from,
            "mileage_defore": filter_obj.mileage_defore,
            "price_from": filter_obj.price_from,
            "price_defore": filter_obj.price_defore,
            "date_release_from": filter_obj.date_release_from,
            "date_release_defore": filter_obj.date_release_defore,
            "create_dttm": filter_obj.create_dttm,
            "update_dttm": filter_obj.update_dttm
        }
        return FilterResponse(**response_data)

# Обновление фильтра
@router.put("/{filter_id}", response_model=FilterResponse)
async def update_filter(filter_id: int, filter_data: FilterUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        filter_obj = await db.get_filter_by_id(filter_id)
        if not filter_obj:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        
        # Обновление полей фильтра
        update_data = filter_data.model_dump(exclude_unset=True, exclude={"equipment_ids"})
        updated_filter = await db.update_filter(filter_id, **update_data)
        
        # Обновление комплектаций, если передан список equipment_ids
        if filter_data.equipment_ids is not None:
            # Удаляем все текущие комплектации
            current_equipment_ids = await db.get_equipment_ids_by_filter(filter_id)
            for equipment_id in current_equipment_ids:
                await db.remove_equipment_from_filter(filter_id, equipment_id)
            # Добавляем новые комплектации
            for equipment_id in filter_data.equipment_ids:
                await db.add_equipment_to_filter(filter_id, equipment_id)
        
        # Формирование ответа
        manufacture = await db.get_manufacture_by_id(updated_filter.manufacture_id) if updated_filter.manufacture_id else None
        model = await db.get_model_by_id(updated_filter.model_id) if updated_filter.model_id else None
        series = await db.get_series_by_id(updated_filter.series_id) if updated_filter.series_id else None
        equipment_ids = await db.get_equipment_ids_by_filter(updated_filter.id)
        equipments = [await db.get_equipment_by_id(eid) for eid in equipment_ids]
        engine_type = await db.get_engine_type_by_id(updated_filter.engine_type_id) if updated_filter.engine_type_id else None
        car_color = await db.get_car_color_by_id(updated_filter.car_color_id) if updated_filter.car_color_id else None

        response_data = {
            "id": updated_filter.id,
            "user_id": updated_filter.user_id,
            "manufacture": manufacture.translated if manufacture else None,
            "model": model.translated if model else None,
            "series": series.translated if series else None,
            "equipment": [eq.translated for eq in equipments if eq],
            "engine_type": engine_type.translated if engine_type else None,
            "drive_type_id": updated_filter.drive_type_id,
            "car_color": car_color.translated if car_color else None,
            "mileage_from": updated_filter.mileage_from,
            "mileage_defore": updated_filter.mileage_defore,
            "price_from": updated_filter.price_from,
            "price_defore": updated_filter.price_defore,
            "date_release_from": updated_filter.date_release_from,
            "date_release_defore": updated_filter.date_release_defore,
            "create_dttm": updated_filter.create_dttm,
            "update_dttm": updated_filter.update_dttm
        }
        return FilterResponse(**response_data)

# Удаление фильтра
@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(filter_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_filter(filter_id)
        if not success:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        # Комплектации автоматически удаляются благодаря ondelete="CASCADE" в filter_equipment
        return None