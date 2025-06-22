import pytest
from httpx import ASGITransport, AsyncClient

from examples.uncaught_error import app


@pytest.fixture(name="test_client")
async def fixture_test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


# TODO: Set these up with the testing handler


async def test_uncaught_error_app_log(
    test_client: AsyncClient,
    log_ctx,
):
    async with log_ctx() as logger:
        with pytest.raises(Exception) as e_info:
            response = await test_client.get("/")


async def test_uncaught_error_access_log(
    test_client: AsyncClient,
    log_ctx,
):
    async with log_ctx() as logger:
        with pytest.raises(Exception) as e_info:
            response = await test_client.get("/")
