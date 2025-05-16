from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
import os
# Database connection (existing SQLite file)
# DATABASE_URL = "sqlite+aiosqlite:///data/vaccination_db.sqlite"
# Azure PostgreSQL connection (updated)
DATABASE_URL = (
    "postgresql+asyncpg://{username}:{password}@{host}:{port}/{dbname}"
    "?ssl=require"  # SSL is mandatory for Azure PostgreSQL
).format(
    username=os.environ["PG_USER"],  # Replace with Azure AD user
    password=os.environ["PG_PASSWORD"],  # Use token for AAD auth
    host=os.environ["PG_HOST"],
    port=os.environ["PG_PORT"],
    dbname=os.environ["PG_DATABASE"],
)

engine = create_async_engine(DATABASE_URL, echo=False)

# Session creation
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base class for ORM models
Base = declarative_base()


async def get_db() -> AsyncSession:  # type: ignore
    async with AsyncSessionLocal() as db:
        async with db.begin():
            yield db
