from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlalchemy.orm import sessionmaker

from database.base import SqlAlchemyBase

__factory = None


async def global_init(user, password, host, port, dbname, delete_db=False):
    global __factory

    if __factory:
        return
    # postgresql+asyncpg для postgres и mysql+aiomysql для mysql
    db_type = "postgresql+asyncpg" if host != "localhost" else "mysql+aiomysql"
    conn_str = f'{db_type}://{user}:{password}@{host}:{port}/{dbname}'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = create_async_engine(conn_str, pool_pre_ping=True)
    

    from . import __all_models
    # Создание всех таблиц
    async with engine.begin() as conn:
        print(f"Registered tables: {SqlAlchemyBase.metadata.tables.keys()}")
        if delete_db:
            await conn.run_sync(SqlAlchemyBase.metadata.drop_all)
        await conn.run_sync(SqlAlchemyBase.metadata.create_all)

    __factory = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )


def create_session() -> AsyncSession:
    global __factory
    return __factory()
