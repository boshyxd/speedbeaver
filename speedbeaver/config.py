import logging
from typing import Any, Literal, TypedDict

import structlog
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from structlog.typing import Processor

from speedbeaver.processor_collection_builder import ProcessorCollectionBuilder

OnOrOff = Literal["ON"] | Literal["OFF"]

LogLevel = (
    Literal["DEBUG"]
    | Literal["INFO"]
    | Literal["WARNING"]
    | Literal["ERROR"]
    | Literal["CRITICAL"]
    | Literal["FATAL"]
)


def extract_from_record(_, __, event_dict):
    """
    Extract thread and process names and add them to the event dict.

    This is primarily for internal use.
    """
    record = event_dict["_record"]
    event_dict["thread_name"] = record.threadName
    event_dict["process_name"] = record.processName
    return event_dict


class LogSettingsArgs(TypedDict):
    json_logs: bool
    opentelemetry: bool
    log_level: LogLevel
    timestamp_format: str
    logger_name: str

    test_mode: bool
    log_file_name: str | None

    processor_override: list[Processor] | None
    propagated_loggers: list[str] | None
    cleared_loggers: list[str] | None


class LogSettings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True)

    json_logs: bool = False
    opentelemetry: bool = False
    log_level: LogLevel = "INFO"
    timestamp_format: str = "iso"
    logger_name: str = "app"

    test_mode: bool = False
    log_file_name: str | None = None

    processor_override: list[Processor] | None = None
    propagated_loggers: list[str] | None = None
    cleared_loggers: list[str] | None = None

    def model_post_init(self, context: Any, /) -> None:
        default_processors = self.get_default_processors()

        shared_processors: list[Processor] = (
            default_processors
            if self.processor_override is None
            else self.processor_override
        )

        # TODO: Figure out how to get file logging

        structlog.configure(
            processors=shared_processors
            + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=not self.test_mode,
        )
        return super().model_post_init(context)

    def get_default_processors(
        self,
    ) -> list[Processor]:
        default_processor_builder = (
            ProcessorCollectionBuilder()
            .add_log_level()
            .add_logger_name()
            .add_positional_arguments()
            .add_callsite_parameters()
            .add_timestamp(format=self.timestamp_format)
            .add_stack_info_renderer()
        )
        if self.json_logs:
            default_processor_builder.add_exception_info()
        if self.opentelemetry:
            default_processor_builder.add_opentelemetry()

        return default_processor_builder.get_processors()

    def _setup_handlers(self, shared_processors: list[Processor]):
        self._stream_handler(shared_processors)
        if self.log_file_name:
            self._file_handler(shared_processors)

        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

    def _stream_handler(
        self, shared_processors: list[Processor]
    ) -> logging.Handler:
        log_renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=True
        )
        if self.settings.JSON_LOGS:
            log_renderer = structlog.processors.JSONRenderer()

        formatter = structlog.stdlib.ProcessorFormatter(
            # These run ONLY on `logging` entries that do NOT originate within
            # structlog.
            foreign_pre_chain=shared_processors,
            # These run on ALL entries after the pre_chain is done.
            processors=[
                # Remove _record & _from_structlog.
                extract_from_record,
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                log_renderer,
            ],
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        return handler

    def _add_file_handler(self, shared_processors: list[Processor]):
        assert self.settings.LOG_FILE_NAME
        log_renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=False
        )
        if self.settings.JSON_LOGS:
            log_renderer = structlog.processors.JSONRenderer()

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
            filename=self.settings.LOG_FILE_NAME
        )
        handler.setFormatter(formatter)
        self.root_logger.addHandler(handler)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return super().settings_customise_sources(
            settings_cls,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            init_settings,
        )
