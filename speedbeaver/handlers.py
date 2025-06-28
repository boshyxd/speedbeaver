import logging
import logging.handlers
import subprocess
import json
import os
from pathlib import Path
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


class TUIStreamHandler(logging.StreamHandler):
    
    def __init__(self, stream=None):
        super().__init__(stream)
        self.tui_process = None
        self._try_start_tui()
    
    def _try_start_tui(self):
        try:
            speedbeaver_dir = os.path.dirname(os.path.dirname(__file__))
            project_root = os.path.dirname(speedbeaver_dir)
            tui_binary = os.path.join(project_root, "speedbeaver-tui")
            
            if os.path.exists(tui_binary):
                self.tui_process = subprocess.Popen(
                    [tui_binary],
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                return
                
            tui_dir = os.path.join(project_root, "go-tui")
            if os.path.exists(tui_dir) and os.path.exists(os.path.join(tui_dir, "main.go")):
                self.tui_process = subprocess.Popen(
                    ["go", "run", "main.go"],
                    cwd=tui_dir,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
        except Exception:
            self.tui_process = None
    
    def emit(self, record):
        if self.tui_process and self.tui_process.stdin:
            try:
                log_data = {
                    "timestamp": record.created,
                    "level": record.levelname,
                    "message": self.format(record),
                    "logger": record.name,
                }
                
                if hasattr(record, 'request_id'):
                    log_data["request_id"] = record.request_id
                
                json_line = json.dumps(log_data) + "\n"
                self.tui_process.stdin.write(json_line)
                self.tui_process.stdin.flush()
                return
            except Exception:
                self.tui_process = None
        
        super().emit(record)
    
    def close(self):
        if self.tui_process:
            try:
                self.tui_process.stdin.close()
                self.tui_process.terminate()
            except Exception:
                pass
            self.tui_process = None
        super().close()


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
            foreign_pre_chain=shared_processors,
            processors=[
                extract_from_record,
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                log_renderer,
            ],
        )
        handler = TUIStreamHandler()
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
    file_name: str | None = None

    def handler(self, shared_processors: list[Processor]):
        if not self.enabled:
            return None
        assert self.file_name

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
            filename=Path(".") / "logs" / self.file_name
        )
        handler.setFormatter(formatter)
        handler.setLevel(self.log_level)
        return handler
