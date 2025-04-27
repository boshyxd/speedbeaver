from collections.abc import Callable
from typing import Any

import pytest
from _pytest.capture import CaptureFixture
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from structlog_fastapi import StructlogMiddleware, get_logger
from structlog_fastapi.config import LogSettingsDefaults

app = FastAPI()
app.add_middleware(
    StructlogMiddleware, log_level="DEBUG", processor_override=[]
)
app.add_middleware(CorrelationIdMiddleware)

logger = get_logger()


@app.get("/")
async def index():
    await logger.info("Hello, world!")
    return {"message": "Hello, world!"}


@pytest.fixture(name="test_client")
async def fixture_test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


async def test_hello_world_app_log(
    capsys: CaptureFixture,
    decode_log: Callable[[str], dict[str, Any]],
    test_client: AsyncClient,
):
    response = await test_client.get("/")
    assert response.status_code == 200

    captured = capsys.readouterr()
    logs = str(captured.err).splitlines()

    print(logs)

    app_log = logs[0]

    app_log_data = decode_log(app_log)

    assert app_log_data.get("logger") == LogSettingsDefaults.LOGGER_NAME
    assert app_log_data.get("event") == "Hello, world!"


async def test_hello_world_access_log(
    capsys: CaptureFixture,
    decode_log: Callable[[str], dict[str, Any]],
    test_client: AsyncClient,
):
    response = await test_client.get("/")
    assert response.status_code == 200

    captured = capsys.readouterr()
    logs = str(captured.err).splitlines()

    access_log = logs[1]

    print(access_log)

    access_log_data = decode_log(access_log)
    assert access_log_data.get("logger") == "structlog_fastapi.access"
    assert access_log_data["http"]["request_id"]
    assert access_log_data["http"]["url"] == 'URL("http://testserver/")'
    assert access_log_data["http"]["status_code"] == 200
