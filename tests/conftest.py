import json
import logging
import os
from typing import Any

import pytest

os.environ.setdefault("JSON_LOGS", "ON")
os.environ.setdefault("TEST_MODE", "ON")


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
        message = json.loads(record)
        return message

    return _decode_log
