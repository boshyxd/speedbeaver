from collections.abc import Callable
from typing import Any

import pytest
from _pytest.capture import CaptureFixture
from httpx import ASGITransport, AsyncClient

from examples.hello_world import app


@pytest.fixture(name="test_client")
async def fixture_test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


# TODO: Fix these to use some testing log handler


async def test_hello_world_app_log(
    capsys: CaptureFixture,
    decode_log: Callable[[str], dict[str, Any]],
    test_client: AsyncClient,
    log_ctx,
):
    async with log_ctx() as logger:
        response = await test_client.get("/")
        assert response.status_code == 200


async def test_hello_world_access_log(
    capsys: CaptureFixture,
    decode_log: Callable[[str], dict[str, Any]],
    test_client: AsyncClient,
    log_ctx,
):
    async with log_ctx() as logger:
        response = await test_client.get("/")
        assert response.status_code == 200
