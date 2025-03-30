from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Фильтры
class FilterCreate(BaseModel):
    user_id: int
    manufacture_id: Optional[int] = None
    model_id: Optional[int] = None
    series_id: Optional[int] = None
    equipment_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    # drive_type_id: Optional[int] = None
    car_color_id: Optional[int] = None
    mileage_from: Optional[int] = None
    mileage_defore: Optional[int] = None  # Предполагается "mileage_before", исправлено в ТЗ как "defore"
    price_from: Optional[int] = None
    price_defore: Optional[int] = None  # То же самое
    date_release_from: Optional[datetime] = None
    date_release_defor: Optional[datetime] = None  # То же самое

class FilterResponse(BaseModel):
    id: int
    manufacture_name: Optional[str] = None
    model_name: Optional[str] = None
    series_name: Optional[str] = None
    equipment_name: Optional[str] = None
    mileage_from: Optional[int] = None
    mileage_defore: Optional[int] = None
    price_from: Optional[int] = None
    price_defore: Optional[int] = None
    date_release_from: Optional[datetime] = None
    date_release_defor: Optional[datetime] = None

# Тарифы
class TariffResponse(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    days_count: Optional[int] = None
    price: Optional[float] = None
    filters_count: Optional[int] = None
    create_dttm: datetime
    update_dttm: datetime

    class Config:
        from_attributes = True

# Подписка
class SubscriptionCreate(BaseModel):
    user_id: int
    tariff_id: int
    subscription_end: datetime

class SubscriptionEdit(BaseModel):
    id: int
    tariff_id: Optional[int] = None
    subscription_end: Optional[datetime] = None

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    tariff: TariffResponse  # Заменяем tariff_id на объект tariff
    subscription_end: Optional[datetime] = None
    create_dttm: datetime
    update_dttm: datetime

    class Config:
        from_attributes = True

# Контакты
class ContactResponse(BaseModel):
    title: str
    url: str
    sequence_number: int

# Операции оплаты
class PayHistoryCreate(BaseModel):
    user_id: int
    price: int
    tariff_id: int
    successfully: bool

class PayHistoryEdit(BaseModel):
    id: int
    successfully: Optional[bool] = None

# Справочники
class ReferenceResponse(BaseModel):
    id: int
    name: str
    translated: str