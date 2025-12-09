"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from app.core.config import settings
from app.core.database import get_session
from app.models import *  # Import all models


# Test database URL - use in-memory SQLite for testing
TEST_DATABASE_URL = settings.database_url



@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    # Only include check_same_thread for SQLite databases
    connect_args = {}
    if "sqlite" in TEST_DATABASE_URL.lower():
        connect_args["check_same_thread"] = False
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args=connect_args,
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def db_session_override(test_session: AsyncSession):
    """Override the get_session dependency with test session."""
    async def override_get_session():
        yield test_session
    
    return override_get_session


@pytest.fixture(scope="function")
def client(test_session, db_session_override):
    """Create a test client for FastAPI."""
    from fastapi.testclient import TestClient
    from main import app
    
    app.dependency_overrides[get_session] = db_session_override
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(test_session, db_session_override):
    """Create an async test client for FastAPI."""
    from httpx import AsyncClient
    from main import app
    
    app.dependency_overrides[get_session] = db_session_override
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

