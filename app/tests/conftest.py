import logging
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi_keycloak_middleware import FastApiUser
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import database_session
from app.core.config import get_settings
from app.main import app as fastapi_app

# Remove JWT and password related imports and variables
default_user_id = "b75365d9-7bf9-4f54-add5-aeab333a087b"
default_user_email = "geralt@wiedzmin.pl"
default_user_first_name = "Geralt"
default_user_last_name = "of Rivia"

# Mock Keycloak token
default_user_access_token = "mock_keycloak_token"

# @pytest.fixture(scope="session")
# def event_loop_policy():
#     return uvloop.EventLoopPolicy()


# @pytest.fixture(scope="session")
# def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     yield loop
#     loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def fixture_setup_new_test_database() -> None:
    worker_name = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    test_db_name = f"test_db_{worker_name}"

    # create new test db using connection to current database
    conn = await database_session._ASYNC_ENGINE.connect()
    await conn.execution_options(isolation_level="AUTOCOMMIT")
    await conn.execute(sqlalchemy.text(f"DROP DATABASE IF EXISTS {test_db_name}"))
    await conn.execute(sqlalchemy.text(f"CREATE DATABASE {test_db_name}"))
    await conn.close()

    session_mpatch = pytest.MonkeyPatch()
    session_mpatch.setenv("DATABASE__DB", test_db_name)
    session_mpatch.setenv("SECURITY__PASSWORD_BCRYPT_ROUNDS", "4")

    # force settings to use now monkeypatched environments
    get_settings.cache_clear()

    # monkeypatch test database engine
    engine = database_session.new_async_engine(get_settings().sqlalchemy_database_uri)

    session_mpatch.setattr(
        database_session,
        "_ASYNC_ENGINE",
        engine,
    )
    session_mpatch.setattr(
        database_session,
        "_ASYNC_SESSIONMAKER",
        async_sessionmaker(engine, expire_on_commit=False),
    )

    # create app tables in test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def fixture_clean_get_settings_between_tests() -> AsyncGenerator[None, None]:
    yield

    get_settings.cache_clear()


@pytest_asyncio.fixture(name="session", scope="function")
async def fixture_session_with_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncSession, None]:
    # we want to monkeypatch get_async_session with one bound to session
    # that we will always rollback on function scope

    connection = await database_session._ASYNC_ENGINE.connect()
    transaction = await connection.begin()

    session = AsyncSession(bind=connection, expire_on_commit=False)

    monkeypatch.setattr(
        database_session,
        "get_async_session",
        lambda: session,
    )

    yield session

    logging.critical("Rolling back transaction")
    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(name="client", scope="function")
async def fixture_client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=fastapi_app)  # type: ignore
    async with AsyncClient(transport=transport, base_url="http://test") as aclient:
        aclient.headers.update({"Host": "localhost"})
        yield aclient


@pytest_asyncio.fixture(name="default_user", scope="function")
async def fixture_default_user() -> FastApiUser:
    return FastApiUser(
        first_name=default_user_first_name,
        last_name=default_user_last_name,
        user_id=default_user_id,
    )


@pytest_asyncio.fixture(name="default_user_headers", scope="function")
def fixture_default_user_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {default_user_access_token}"}
