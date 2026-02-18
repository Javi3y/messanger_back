from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import os

from src.base.ports.database import AsyncDatabase

Base = declarative_base()


class AsyncSqlalchemyDatabase(AsyncDatabase):
    """Async postgres database connection manager"""

    def __init__(self, database_url: str):
        super().__init__(database_url)
        self.engine = create_async_engine(
            database_url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            future=True,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        # self.session = self.SessionLocal()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        async with self.SessionLocal() as session:
            yield session

    async def close(self) -> None:
        """Close the underlying SQLAlchemy engine."""
        if self.engine:
            await self.engine.dispose()
