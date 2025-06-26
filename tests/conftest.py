import logging
import os
import uuid
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

import orjson
import pytest
import structlog
from structlog.stdlib import BoundLogger

from speedbeaver.methods import get_logger

os.environ.setdefault("TEST__ENABLED", "True")

logging.getLogger("asyncio").setLevel(logging.ERROR)

LogLine = dict[str, Any]


def _cleanup_handlers_for_logger(logger: logging.Logger | logging.PlaceHolder):
    handlers = getattr(logger, "handlers", [])
    for handler in handlers:
        logging.root.removeHandler(handler)


@pytest.fixture(scope="session", autouse=True)
async def cleanup_logging_handlers(log_dir: Path):
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
    def _decode_log(record: str) -> LogLine:
        message = orjson.loads(record)
        return message

    return _decode_log


@pytest.fixture(name="test_id", scope="function")
def fixture_test_id():
    yield uuid.uuid4().hex


@pytest.fixture(name="logger", scope="function")
async def fixture_logger(request, test_id: str):
    logger = get_logger("speedbeaver.test")
    context = {"test_id": test_id, "test_name": request.node.name}
    structlog.contextvars.bind_contextvars(**context)
    log = logger.bind(**context)
    result = "fail"
    try:
        yield log
        result = "success"
    except Exception as e:
        await log.aexception(str(e))
        raise
    finally:
        await log.ainfo("Test complete.", result=result)
    structlog.contextvars.clear_contextvars()


@pytest.fixture(name="parse_log_file", scope="function")
def fixture_parse_log_file(
    logger: BoundLogger, test_id: str, decode_log: Callable[[str], LogLine]
):
    async def parse_log_file(path: os.PathLike) -> tuple[list[LogLine], str]:
        """
        Parses a given log file for log lines matching a given test ID
        """
        # This is important because it saves the test ID in the logs
        await logger.ainfo("Scenario complete, parsing logs.")
        log_lines: list[LogLine]
        with open(path) as log_file:
            log_lines = [decode_log(line) for line in log_file.readlines()]

        log_lines_by_request_id: dict[str, list[LogLine]] = defaultdict(
            list[LogLine]
        )
        matched_request_id: str = ""
        for log_line in log_lines:
            request_id = log_line.get("request_id")
            if request_id is None:
                continue
            log_lines_by_request_id[request_id].append(log_line)

            if log_line.get("test_id") == test_id and not matched_request_id:
                matched_request_id = request_id
        log_lines = log_lines_by_request_id.get(matched_request_id, [])
        return log_lines, matched_request_id

    return parse_log_file


@pytest.fixture(name="log_dir", scope="session")
def fixture_log_dir():
    return Path("logs")
