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
    drive_type_id: Optional[int] = None
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
    name: str
    description: Optional[str] = None
    filter_count: int
    subscription_end: datetime

# Тарифы
class TariffResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    days_count: int
    price: int
    filter_count: int

# Контакты
class ContactResponse(BaseModel):
    title: str
    url: str
    sequence_number: int

# Операции оплаты
class PayHistoryCreate(BaseModel):
    id: int
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