import os
from sqlalchemy import Column, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/users.db")

engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class UserRow(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    salt = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    scopes = Column(String, nullable=False)  # space-separated


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
