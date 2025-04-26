from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import telegram_auth, admin_auth
from api.models import FilterCreate, FilterResponse
from database import DBApi
from typing import List
from functions.new_filter import send_car_by_filter

router = APIRouter(prefix="/filter", tags=["Filters"])

@router.post("/create", response_model=FilterResponse)
async def create_filter(filter_data: FilterCreate, user_id: int = Depends(telegram_auth)):
    async with DBApi() as db:
        # Проверка подписки и лимита фильтров
        subscription = await db.get_active_subscription_by_user(user_id)
        if not subscription:
            raise HTTPException(status_code=403, detail="У вас нет активной подписки")
        
        tariff = await db.get_tariff_by_id(subscription.tariff_id)
        filters_count = await db.get_filters_count_by_user(user_id)
        if filters_count >= tariff.filters_count:
            raise HTTPException(status_code=403, detail="Превышен лимит фильтров. Удалите старые или обновите подписку")
        
        # Создание фильтра без equipment_ids
        filter_obj = await db.create_filter(user_id, **filter_data.model_dump(exclude={"equipment_ids"}))
        
        # Добавление комплектаций
        for equipment_id in filter_data.equipment_ids:
            await db.add_equipment_to_filter(filter_obj.id, equipment_id)
        
        # Подготовка ответа
        filter_fetched = await db.get_filter_by_id(filter_obj.id)
        manufacture = await db.get_manufacture_by_id(filter_fetched.manufacture_id) if filter_fetched.manufacture_id else None
        model = await db.get_model_by_id(filter_fetched.model_id) if filter_fetched.model_id else None
        series = await db.get_series_by_id(filter_fetched.series_id) if filter_fetched.series_id else None
        equipment_ids = await db.get_equipment_ids_by_filter(filter_fetched.id)
        equipments = [await db.get_equipment_by_id(eid) for eid in equipment_ids]
        engine_type = await db.get_engine_type_by_id(filter_fetched.engine_type_id) if filter_fetched.engine_type_id else None
        car_color = await db.get_car_color_by_id(filter_fetched.car_color_id) if filter_fetched.car_color_id else None

        response_data = {
            "id": filter_fetched.id,
            "manufacture": manufacture.translated if manufacture else None,
            "model": model.translated if model else None,
            "series": series.translated if series else None,
            "equipment": [eq.translated for eq in equipments if eq],
            "engine_type": engine_type.translated if engine_type else None,
            "drive_type_id": filter_fetched.drive_type_id,
            "car_color": car_color.translated if car_color else None,
            "mileage_from": filter_fetched.mileage_from,
            "mileage_defore": filter_fetched.mileage_defore,
            "price_from": filter_fetched.price_from,
            "price_defore": filter_fetched.price_defore,
            "date_release_from": filter_fetched.date_release_from,
            "date_release_defore": filter_fetched.date_release_defore,
        }

        # Отправка автомобилей по фильтру
        await send_car_by_filter(user_id, filter_obj.id)
        return FilterResponse(**response_data)

@router.get("/list", response_model=List[FilterResponse])
async def get_filters(auth_user_id: int = Depends(telegram_auth)):
    filters_data = []
    async with DBApi() as db:
        filters = await db.get_filters_by_user(auth_user_id)
        for i in filters:
            manufacture = await db.get_manufacture_by_id(i.manufacture_id) if i.manufacture_id else None
            model = await db.get_model_by_id(i.model_id) if i.model_id else None
            series = await db.get_series_by_id(i.series_id) if i.series_id else None
            equipment_ids = await db.get_equipment_ids_by_filter(i.id)
            equipments = [await db.get_equipment_by_id(eid) for eid in equipment_ids]
            engine_type = await db.get_engine_type_by_id(i.engine_type_id) if i.engine_type_id else None
            car_color = await db.get_car_color_by_id(i.car_color_id) if i.car_color_id else None
            filters_data.append(
                {
                    "id": i.id,
                    "manufacture": manufacture.translated if manufacture else None,
                    "model": model.translated if model else None,
                    "series": series.translated if series else None,
                    "equipment": [eq.translated for eq in equipments if eq],
                    "engine_type": engine_type.translated if engine_type else None,
                    "drive_type_id": i.drive_type_id,
                    "car_color": car_color.translated if car_color else None,
                    "mileage_from": i.mileage_from,
                    "mileage_defore": i.mileage_defore,
                    "price_from": i.price_from,
                    "price_defore": i.price_defore,
                    "date_release_from": i.date_release_from,
                    "date_release_defore": i.date_release_defore,
                }
            )
    return [FilterResponse(**f) for f in filters_data]

@router.delete("/{id}")
async def delete_filter(id: int, user_id: bool = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        filter = await db.get_filter_by_id(id)
        if not filter or filter.user_id != user_id:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        success = await db.delete_filter(id)
        if not success:
            raise HTTPException(status_code=404, detail="Фильтр не найден")
        return {"success": True}