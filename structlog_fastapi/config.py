from enum import Enum
from functools import cache

from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class LogSettings(BaseSettings):
    JSON_LOGS: bool = False
    # TODO: Fix this so that environment variables will work
    LOG_LEVEL: LogLevel = LogLevel.INFO
    TIMESTAMP_FORMAT: str = "iso"
    LOGGER_NAME: str = "app"


@cache
def get_settings() -> LogSettings:
    return LogSettings()


settings = get_settings()
