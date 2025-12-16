from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import POSTGRES_URL


DATABASE_URL = POSTGRES_URL

async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


class Base(DeclarativeBase):  # New
    pass
