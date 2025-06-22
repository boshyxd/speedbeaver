import logging
import logging.handlers
from typing import Any

import orjson
import structlog
from pydantic.main import BaseModel
from structlog.typing import Processor

from speedbeaver.common import LogLevel


def extract_from_record(_, __, event_dict):
    """
    Extract thread and process names and add them to the event dict.

    This is primarily for internal use.
    """
    record = event_dict["_record"]
    event_dict["thread_name"] = record.threadName
    event_dict["process_name"] = record.processName
    return event_dict


def json_serializer(__obj: Any, /, **kwargs):
    return orjson.dumps(__obj, **kwargs).decode()


json_renderer = structlog.processors.JSONRenderer(serializer=json_serializer)


class LogHandlerSettings(BaseModel):
    json_logs: bool = False
    log_level: LogLevel = "DEBUG"
    enabled: bool = False


class LogStreamSettings(LogHandlerSettings):
    enabled: bool = True
    colors: bool = True

    def handler(self, shared_processors: list[Processor]):
        if not self.enabled:
            return None
        log_renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=self.colors
        )
        if self.json_logs:
            log_renderer = json_renderer
            shared_processors += [structlog.processors.format_exc_info]

        formatter = structlog.stdlib.ProcessorFormatter(
            # These run ONLY on `logging` entries that do NOT originate within
            # structlog.
            foreign_pre_chain=shared_processors,
            # These run on ALL entries after the pre_chain is done.
            processors=[
                extract_from_record,
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                log_renderer,
            ],
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(self.log_level)
        return handler


class LogFileSettings(LogHandlerSettings):
    file_name: str | None = None

    def handler(self, shared_processors: list[Processor]):
        if not self.enabled:
            return None
        assert self.file_name
        log_renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=False
        )
        if self.json_logs:
            log_renderer = json_renderer
            shared_processors += [structlog.processors.format_exc_info]
        formatter = structlog.stdlib.ProcessorFormatter(
            # These run ONLY on `logging` entries that do NOT originate within
            # structlog.
            foreign_pre_chain=shared_processors,
            # These run on ALL entries after the pre_chain is done.
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                log_renderer,
            ],
        )
        handler = logging.handlers.WatchedFileHandler(filename=self.file_name)
        handler.setFormatter(formatter)
        handler.setLevel(self.log_level)
        return handler


class LogTestSettings(LogHandlerSettings):
    def handler(self, shared_processors: list[Processor]):
        if not self.enabled:
            return None

        log_renderer: structlog.types.Processor = json_renderer
        shared_processors += [structlog.processors.format_exc_info]
        formatter = structlog.stdlib.ProcessorFormatter(
            # These run ONLY on `logging` entries that do NOT originate within
            # structlog.
            foreign_pre_chain=shared_processors,
            # These run on ALL entries after the pre_chain is done.
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                log_renderer,
            ],
        )
        handler = logging.handlers.WatchedFileHandler(
            filename="test.log", mode="w"
        )
        handler.setFormatter(formatter)
        handler.setLevel(self.log_level)
        return handler

    pass
