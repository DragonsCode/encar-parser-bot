from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import DBApi
from fastapi_pagination import Page  # Импортируем Page для пагинации
from fastapi_pagination.ext.sqlalchemy import paginate  # Импортируем paginate для SQLAlchemy

router = APIRouter(prefix="/admin/settings", tags=["Admin - Settings"])

# Модель для создания/обновления настройки
class SettingCreate(BaseModel):
    key: str
    value: str
    name: Optional[str] = None
    description: Optional[str] = None

# Модель для обновления настройки
class SettingUpdate(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

# Модель для ответа
class SettingResponse(BaseModel):
    id: int
    key: str
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание или обновление настройки
@router.post("/", response_model=SettingResponse, status_code=status.HTTP_201_CREATED)
async def set_setting(setting: SettingCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        setting_data = await db.set_setting(
            key=setting.key,
            value=setting.value,
            name=setting.name,
            description=setting.description
        )
        if not setting_data:
            raise HTTPException(status_code=400, detail="Ошибка при создании/обновлении настройки")
        return setting_data

# Получение всех настроек с пагинацией
@router.get("/", response_model=Page[SettingResponse])
async def get_all_settings(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        # Используем новый метод get_all_settings_query для получения SQLAlchemy-запроса
        query = await db.get_all_settings_query()
        return await paginate(db._sess, query)

# Получение настройки по ключу
@router.get("/key/{key}", response_model=SettingResponse)
async def get_setting_by_key(key: str, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        setting = await db.get_setting_by_key(key)
        if not setting:
            raise HTTPException(status_code=404, detail="Настройка не найдена")
        return setting

# Получение настройки по ID
@router.get("/{setting_id}", response_model=SettingResponse)
async def get_setting(setting_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        setting = await db.get_setting_by_id(setting_id)
        if not setting:
            raise HTTPException(status_code=404, detail="Настройка не найдена")
        return setting

# Обновление настройки по ID
@router.put("/{setting_id}", response_model=SettingResponse)
async def update_setting(setting_id: int, setting: SettingUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_setting = await db.update_setting(setting_id, **setting.dict(exclude_unset=True))
        if not updated_setting:
            raise HTTPException(status_code=404, detail="Настройка не найдена")
        return updated_setting

# Удаление настройки по ID
@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(setting_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_setting(setting_id)
        if not success:
            raise HTTPException(status_code=404, detail="Настройка не найдена")
        return None