import shutil
from datetime import datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from examples.hello_world import app


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
    log_ctx,
    test_log_file_path: Path,
):
    async with log_ctx() as logger:
        response = await test_client.get("/")

    raise AssertionError("Need this to test changes")


async def test_hello_world_access_log(
    test_client: AsyncClient,
    log_ctx,
    test_log_file_path: Path,
):
    async with log_ctx() as logger:
        response = await test_client.get("/")

    raise AssertionError("Need this to test changes")
