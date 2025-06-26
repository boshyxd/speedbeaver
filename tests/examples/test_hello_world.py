import os
import shutil
from collections.abc import Callable, Coroutine
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from structlog.stdlib import BoundLogger

from examples.hello_world import app
from tests.conftest import LogLine


@pytest.fixture(name="test_log_file_path", scope="module")
def fixture_test_log_file_path(log_dir: Path):
    return log_dir / "hello_world.test.log"


@pytest.fixture(scope="module", autouse=True)
def archive_test_logs(test_log_file_path: Path):
    yield
    shutil.move(
        test_log_file_path,
        test_log_file_path.parent
        / f"{datetime.now().isoformat()}.{test_log_file_path.name}",
    )


@pytest.fixture(name="test_client")
async def fixture_test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


async def test_hello_world_app_log(
    test_client: AsyncClient,
    test_id: str,
    logger: BoundLogger,
    test_log_file_path: Path,
    parse_log_file: Callable[[os.PathLike], Coroutine[Any, Any, list[LogLine]]],
):
    response = await test_client.get("/")
    assert response.status_code == 200

    log_lines = await parse_log_file(test_log_file_path)

    assert log_lines[0].get("event") == "Hello, world!"


async def test_hello_world_access_log(
    test_client: AsyncClient,
    test_id: str,
    logger: BoundLogger,
    test_log_file_path: Path,
    decode_log,
):
    response = await test_client.get("/")
    assert response.status_code == 200
