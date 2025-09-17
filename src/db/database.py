from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import DATABASE_URL


class DatabaseSessionManager:
    _engine = None
    _sessionmaker = None

    def __init__(self, db_uri: str | URL):
        self._engine = create_async_engine(
            url=db_uri,
            connect_args={
            #     "ssl": settings.DB_SSL_CONTEXT,
            "server_settings": {
                    "application_name": f"besmedia_web_prod",
                },
	    },
            pool_size=100,
            pool_recycle=3600,
            max_overflow=5,
        )
        self._sessionmaker = async_sessionmaker(
            autoflush=False,
            expire_on_commit=False,
            bind=self._engine,
            autocommit=False,
        )

    async def close(self) -> None:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


db_session_manager = DatabaseSessionManager(
    db_uri=DATABASE_URL,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db_session_manager.session() as session:
        yield session
