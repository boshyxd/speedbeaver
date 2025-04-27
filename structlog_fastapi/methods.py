import structlog

from structlog_fastapi.config import LogSettingsDefaults


def get_logger(
    name: str = LogSettingsDefaults.LOGGER_NAME,
) -> structlog.stdlib.AsyncBoundLogger:
    return structlog.get_logger(name)
