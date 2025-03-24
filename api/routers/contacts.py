from fastapi import APIRouter, Depends
from api.dependencies import telegram_auth
from api.models import ContactResponse
from database import DBApi
from typing import List

router = APIRouter(prefix="/contact", tags=["Contacts"])

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(user_id: int = Depends(telegram_auth)):
    """
    Depends on telegram_auth
    """
    async with DBApi() as db:
        contacts = await db.get_all_contacts()
        return contacts