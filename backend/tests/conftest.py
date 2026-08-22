"""Pytest fixtures for Sentinel AI testing."""
import pytest
import pytest_asyncio
import tempfile
import os
import io
import pandas as pd
import numpy as np
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.models.base import Base
from backend.app.db.session import get_db
from backend.app.core.session_store import session_store

# Shared in-memory SQLite database across all sessions for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    """Initializes schema before every test and cleans up afterward."""
    session_store.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    session_store.clear()


@pytest_asyncio.fixture
async def async_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP Client with database dependency overridden."""
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Synchronous TestClient with database dependency overridden for legacy tests."""
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def temp_dir():
    """Provides a clean temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def sample_valid_df():
    """Returns a valid small fraud dataset DataFrame."""
    np.random.seed(42)
    n_rows = 100
    return pd.DataFrame({
        "trans_num": [f"tx_{i:04d}" for i in range(n_rows)],
        "trans_date_trans_time": pd.date_range("2020-01-01", periods=n_rows, freq="h").astype(str),
        "cc_num": [1000 + (i % 10) for i in range(n_rows)],
        "category": np.random.choice(["grocery_pos", "shopping_net", "entertainment"], size=n_rows),
        "amt": np.random.uniform(5.0, 500.0, size=n_rows).round(2),
        "city": ["New York"] * n_rows,
        "is_fraud": [1 if i < 3 else 0 for i in range(n_rows)]  # 3% fraud rate (severe imbalance)
    })
