import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from api.dependencies import telegram_auth, admin_auth
from api.routers import filters, subscriptions, tariffs, contacts, payhistory, references
from api.admin import car, contacts as admin_contacts, filters as admin_filters, payhistory as admin_payhistory, settings, subscription, tariffs as admin_tariffs, users
from database.db_session import global_init
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Lifespan для инициализации и завершения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: инициализация базы данных
    print("Инициализация базы данных...")
    await global_init(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        delete_db=False
    )
    print("База данных успешно инициализирована")
    yield
    # Shutdown: завершение работы (опционально)
    print("Завершение работы сервера")

app = FastAPI(
    title="Car Parser API",
    description="API для управления фильтрами, подписками и справочниками",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем пагинацию
add_pagination(app)

# Подключаем роутеры
app.include_router(filters.router)
app.include_router(subscriptions.router)
app.include_router(tariffs.router)
app.include_router(contacts.router)
app.include_router(payhistory.router)
app.include_router(references.router)

# Подключаем роутеры админ-панели
app.include_router(car.router)
app.include_router(admin_contacts.router)
app.include_router(admin_filters.router)
app.include_router(admin_payhistory.router)
app.include_router(settings.router)
app.include_router(subscription.router)
app.include_router(admin_tariffs.router)
app.include_router(users.router)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены (можно указать конкретные)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

# Тестовый эндпоинт для проверки работоспособности
@app.get("/")
async def root():
    return {"message": "FastAPI сервер работает!"}

@app.get("/test-telegram-auth")
async def test_telegram_auth(user_id: int = Depends(telegram_auth)):
    return {"message": f"Вы авторизованы как пользователь Telegram с ID {user_id}", "user_id": user_id}

@app.get("/test-admin-auth")
async def test_admin_auth(is_admin: bool = Depends(admin_auth)):
    return {"message": "Вы авторизованы как администратор"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)