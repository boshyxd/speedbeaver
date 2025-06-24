from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from examples.hello_world import app


@pytest.fixture(name="test_client")
async def fixture_test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


async def test_hello_world_app_log(
    test_client: AsyncClient,
    log_ctx,
    log_dir: Path,
):
    async with log_ctx() as logger:
        response = await test_client.get("/")

    raise AssertionError("Need this to test changes")


async def test_hello_world_access_log(
    test_client: AsyncClient,
    log_ctx,
    log_dir: Path,
):
    async with log_ctx() as logger:
        response = await test_client.get("/")

    raise AssertionError("Need this to test changes")
