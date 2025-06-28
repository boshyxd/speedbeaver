import os
import shutil
from collections.abc import Callable, Coroutine
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from structlog.stdlib import BoundLogger

from examples.uncaught_error import app
from tests.conftest import LogLine


@pytest.fixture(name="test_log_file_path", scope="module")
def fixture_test_log_file_path(log_dir: Path):
    return log_dir / "uncaught_error.test.log"


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


# TODO: Figure out if there's a way of testing a running server

# @pytest.fixture(name="uvicorn_server", scope="module", autouse=True)
# async def fixture_unicorn_server():
#     config = uvicorn.Config(app, port=8000)
#     server = uvicorn.Server(config)
#     cancel_handle = asyncio.ensure_future(server.serve())
#     await asyncio.sleep(0.1)
#     try:
#         yield server
#     finally:
#         await server.shutdown()
#         cancel_handle.cancel()
#
#
# @pytest.fixture(name="integration_test_client", scope="module")
# async def fixture_integration_test_client():
#     async with AsyncClient(base_url="http://localhost:8000") as client:
#         yield client


async def test_uncaught_error_app_log(
    test_client: AsyncClient,
    logger: BoundLogger,
    test_log_file_path: Path,
    parse_log_file: Callable[
        [os.PathLike], Coroutine[Any, Any, tuple[list[LogLine], str]]
    ],
):
    with pytest.raises(NotImplementedError):
        await test_client.get("/")

    log_lines, matched_request_id = await parse_log_file(test_log_file_path)

    assert log_lines[0].get("event") == "Uncaught exception"
    for log_line in log_lines:
        assert log_line.get("request_id") == matched_request_id


async def test_uncaught_error_access_log(
    test_client: AsyncClient,
    test_log_file_path: Path,
    parse_log_file: Callable[
        [os.PathLike], Coroutine[Any, Any, tuple[list[LogLine], str]]
    ],
):
    with pytest.raises(NotImplementedError):
        await test_client.get("/")

    log_lines, matched_request_id = await parse_log_file(test_log_file_path)

    assert log_lines[1].get("event") == '127.0.0.1:123 - "GET / HTTP/1.1" 500'
    for log_line in log_lines:
        assert log_line.get("request_id") == matched_request_id


# async def test_uncaught_error_response(
#     integration_test_client: AsyncClient,
#     test_log_file_path: Path,
#     parse_log_file: Callable[
#         [os.PathLike], Coroutine[Any, Any, tuple[list[LogLine], str]]
#     ],
# ):
#     await integration_test_client.get("/")