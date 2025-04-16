from pathlib import Path

import jwt
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from requests import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.oauth2 import create_access_token
from app.main import create_app
from app.models.database import Base, get_db

# Database connection (existing SQLite file)
DATABASE_URL = "sqlite+aiosqlite:///data/test_vaccination_db.sqlite"

engine = create_async_engine(DATABASE_URL, echo=False)

# Session creation
TestingAsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Testing secret
SECRET_KEY = "760e1f0c95052fe205f6189f6ad153ca3758b17bb8d9e0d4f78602894e448517"
ALGORITHM = "HS256"


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    """
    Drop and recreate all tables before each test, then populate them with data.
    """
    async with engine.begin() as conn:
        # 1) Drop & create tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # 2) Load seed data from SQL script (optional)
        sql_file = Path("./data/data.sql")
        if not sql_file.exists():
            raise FileNotFoundError("data.sql not found")

        script = sql_file.read_text()

        # Split statements on semicolons, strip whitespace, and execute each
        for statement in script.split(";"):
            stmt = statement.strip()
            if stmt:
                await conn.execute(text(stmt))

    # The fixture yields here, so tests can run with the fresh, seeded DB
    yield

    # Optionally drop all tables again after each test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(init_test_db) -> AsyncSession:  # type: ignore
    """
    Return a new database session for each test function,
    using the test engine.
    """
    async with TestingAsyncSessionLocal() as db:
        # async with db.begin():
        yield db


@pytest_asyncio.fixture
async def test_app(session: AsyncSession) -> FastAPI:  # type: ignore
    """
    Override FastAPI's get_db so that it yields our test session
    instead of creating a brand new one from the real DB.
    """

    # Create a brand-new test app (i.e. skip middleware, etc.)
    _app = create_app(test=True)

    _app.state.secret_key = SECRET_KEY

    async def _override_get_db():
        yield session

    _app.dependency_overrides[get_db] = _override_get_db

    # Yield the actual app to the test
    yield _app

    _app.dependency_overrides.clear()


# I have investigated and it seems the test data is persisted into my dev database tables instead of my test database. Therefore, it seems the `override_get_db_fixture` did not override the dependencies on the global app from `main.py`. I have narrowed down the issue so how can I fix this?


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncClient:  # type: ignore
    """
    Return an HTTPX AsyncClient that points to our FastAPI app.
    """
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(async_client: AsyncClient) -> tuple[dict, dict]:
    user_data = {
        "nric": "S9999999J",
        "first_name": "john",
        "last_name": "doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-01",  # 35 years old
        "gender": "M",
        "postal_code": "545078",
        "password": "password123",
        "password_confirm": "password123",
    }

    res: Response = await async_client.post(
        "/signup",
        json=user_data,
    )

    assert res.status_code == 201

    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user, user_data


@pytest_asyncio.fixture
async def token(test_app: FastAPI, test_user: tuple[dict, dict]) -> str:
    # 1) Manually create a request object
    test_scope = {"app": test_app, "type": "http"}
    request = Request(test_scope)

    # 2) Ensure test_app.state.secret_key is set (or rely on startup)
    test_app.state.secret_key = SECRET_KEY

    return create_access_token(request, data={"user_id": test_user[0]["id"]})


@pytest_asyncio.fixture
async def authorized_client(async_client: AsyncClient, token: str) -> AsyncClient:
    async_client.headers = {**async_client.headers, "Authorization": f"Bearer {token}"}

    return async_client


@pytest_asyncio.fixture
async def authorized_client_for_no_vaccine_recommendations(async_client: AsyncClient):
    user_data = {"username": "jane.doe@example.com", "password": "password123"}
    res: Response = await async_client.post(
        "/login",
        data=user_data,
    )

    assert res.status_code == 200

    token = res.json().get("access_token")

    async_client.headers = {
        **async_client.headers,
        "Authorization": f"Bearer {token}",
    }

    return async_client


@pytest_asyncio.fixture
async def authorized_client_for_vaccine_records(async_client: AsyncClient):
    user_data = {"username": "test.user@example.com", "password": "testpassword123"}
    res: Response = await async_client.post("/login", data=user_data)

    assert res.status_code == 200

    token = res.json().get("access_token")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    id = payload.get("user_id")

    async_client.headers = {
        **async_client.headers,
        "user_id": str(id),
        "Authorization": f"Bearer {token}",
    }

    return async_client


@pytest_asyncio.fixture
async def authorized_client_for_scheduling(async_client: AsyncClient):
    user_data = {
        "username": "test_2@example.com",
        "password": "Password123",
    }
    res: Response = await async_client.post("/login", data=user_data)
    token = res.json().get("access_token")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    id = payload.get("user_id")

    async_client.headers = {
        **async_client.headers,
        "user_id": str(id),
        "Authorization": f"Bearer {token}",
    }

    return async_client
