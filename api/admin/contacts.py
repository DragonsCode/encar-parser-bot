from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import admin_auth
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import DBApi
from fastapi_pagination import Page  # Импортируем Page для пагинации
from fastapi_pagination.ext.sqlalchemy import paginate  # Импортируем paginate для SQLAlchemy

router = APIRouter(prefix="/admin/contacts", tags=["Admin - Contacts"])

# Модель для создания записи
class ContactCreate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    sequence_number: Optional[int] = None

# Модель для обновления записи
class ContactUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    sequence_number: Optional[int] = None

# Модель для ответа
class ContactResponse(BaseModel):
    id: int
    title: Optional[str] = None
    url: Optional[str] = None
    sequence_number: Optional[int] = None
    create_dttm: datetime
    update_dttm: datetime

# Создание контакта
@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(contact: ContactCreate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        contact_data = await db.create_contact(
            title=contact.title,
            url=contact.url,
            sequence_number=contact.sequence_number
        )
        if not contact_data:
            raise HTTPException(status_code=400, detail="Ошибка при создании контакта")
        return contact_data

# Получение всех контактов с пагинацией
@router.get("/", response_model=Page[ContactResponse])
async def get_all_contacts(is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        # Используем новый метод get_all_contacts_query для получения SQLAlchemy-запроса
        query = await db.get_all_contacts_query()
        return await paginate(db._sess, query)

# Получение контакта по ID
@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        contact = await db.get_contact_by_id(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Контакт не найден")
        return contact

# Обновление контакта
@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        updated_contact = await db.update_contact(contact_id, **contact.dict(exclude_unset=True))
        if not updated_contact:
            raise HTTPException(status_code=404, detail="Контакт не найден")
        return updated_contact

# Удаление контакта
@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int, is_admin: bool = Depends(admin_auth)):
    async with DBApi() as db:
        success = await db.delete_contact(contact_id)
        if not success:
            raise HTTPException(status_code=404, detail="Контакт не найден")
        return None