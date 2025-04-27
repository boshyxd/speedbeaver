from collections.abc import Callable
from logging import LogRecord
from typing import Any

import pytest
from _pytest.logging import LogCaptureFixture
from httpx import ASGITransport, AsyncClient
from starlette.requests import URL

from examples.uncaught_error import app


@pytest.fixture(name="test_client")
async def fixture_test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.mark.xfail
async def test_uncaught_error_app_log(
    caplog: LogCaptureFixture,
    decode_log: Callable[[LogRecord], dict[str, Any]],
    test_client: AsyncClient,
):
    with pytest.raises(Exception) as e_info:
        response = await test_client.get("/")
        pass

    app_log = caplog.records[0]

    assert app_log.name == "structlog_fastapi.error"
    app_log_data = decode_log(app_log)
    assert app_log_data.get("event") == "Hello, world!"


@pytest.mark.xfail
async def test_uncaught_error_access_log(
    caplog: LogCaptureFixture,
    decode_log: Callable[[LogRecord], dict[str, Any]],
    test_client: AsyncClient,
):
    response = await test_client.get("/")
    assert response.status_code == 200

    access_log = caplog.records[1]

    assert access_log.name == "structlog_fastapi.access"
    access_log_data = decode_log(access_log)
    assert access_log_data["http"]["request_id"]
    assert access_log_data["http"]["url"] == URL("http://testserver/")
    assert access_log_data["http"]["status_code"] == 200
