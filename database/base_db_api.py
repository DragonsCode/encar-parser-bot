import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from database.db_session import create_session


class BaseDBApi:
    _sess: AsyncSession

    def __init__(self):
        self._sess = create_session()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.close()  # Ждем закрытия сессии

    async def close(self):
        if self._sess:
            await self._sess.close()
