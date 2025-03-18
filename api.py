from fastapi import FastAPI, Depends
from api.dependencies import telegram_auth, admin_auth
from api.routers import filters, subscriptions, tariffs, contacts, payhistory, references

app = FastAPI(
    title="Car Parser API",
    description="API для управления фильтрами, подписками и справочниками",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(filters.router)
app.include_router(subscriptions.router)
app.include_router(tariffs.router)
app.include_router(contacts.router)
app.include_router(payhistory.router)
app.include_router(references.router)

# Тестовый эндпоинт для проверки работоспособности
@app.get("/")
async def root():
    return {"message": "FastAPI сервер работает!"}

@app.get("/test-telegram-auth")
async def test_telegram_auth(user_id: int = Depends(telegram_auth)):
    return {"message": f"Вы авторизованы как пользователь Telegram с ID {user_id}"}

@app.get("/test-admin-auth")
async def test_admin_auth(is_admin: bool = Depends(admin_auth)):
    return {"message": "Вы авторизованы как администратор"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)