import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

import orjson
import pytest

from speedbeaver.methods import get_logger

os.environ.setdefault("TEST__ENABLED", "True")


def _cleanup_handlers_for_logger(logger: logging.Logger | logging.PlaceHolder):
    handlers = getattr(logger, "handlers", [])
    for handler in handlers:
        logging.root.removeHandler(handler)


@pytest.fixture(scope="session", autouse=True)
async def cleanup_logging_handlers():
    try:
        yield
    finally:
        loggers = [logging.getLogger()] + list(
            logging.Logger.manager.loggerDict.values()
        )
        for logger in loggers:
            _cleanup_handlers_for_logger(logger)


@pytest.fixture(name="decode_log")
def fixture_decode_log():
    def _decode_log(record: str) -> dict[str, Any]:
        message = orjson.loads(record)
        return message

    return _decode_log


@pytest.fixture(name="log_ctx", scope="function")
def fixture_log_ctx(request):
    @asynccontextmanager
    async def _log_ctx():
        logger = get_logger("speedbeaver.test")
        log = logger.bind(test_id=uuid.uuid4().hex, test_name=request.node.name)

        try:
            yield log
            await log.ainfo("Test complete.")
        except Exception as e:
            await log.aexception(str(e))

    return _log_ctx
