from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import DBApi

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

# Модель для создания записи
class UserCreate(BaseModel):
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None

# Модель для обновления записи
class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None

# Модель для ответа
class UserResponse(BaseModel):
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание пользователя
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        user_data = await db.create_user(
            id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        if not user_data:
            raise HTTPException(status_code=400, detail="Ошибка при создании пользователя")
        return user_data

# Получение всех пользователей
@router.get("/", response_model=List[UserResponse])
async def get_all_users(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        users = await db.get_all_users()
        return users

# Получение пользователя по ID
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        user = await db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return user

# Обновление пользователя
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_user = await db.update_user(user_id, **user.dict(exclude_unset=True))
        if not updated_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return updated_user

# Удаление пользователя
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return None