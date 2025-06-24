import logging
from typing import TypedDict

import structlog
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from structlog.typing import Processor
from typing_extensions import NotRequired

from speedbeaver.common import LogLevel
from speedbeaver.handlers import (
    LogFileSettings,
    LogStreamSettings,
    LogTestSettings,
)
from speedbeaver.methods import get_logger
from speedbeaver.processor_collection_builder import ProcessorCollectionBuilder


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
    opentelemetry: NotRequired[bool]
    timestamp_format: NotRequired[str]
    logger_name: NotRequired[str]
    log_level: NotRequired[LogLevel | None]

    stream: NotRequired[LogStreamSettings]
    file: NotRequired[LogFileSettings]
    test: NotRequired[LogTestSettings]

    processor_override: NotRequired[list[Processor] | None]
    propagated_loggers: NotRequired[list[str] | None]
    cleared_loggers: NotRequired[list[str] | None]


class LogSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

    stream: LogStreamSettings = LogStreamSettings()
    file: LogFileSettings = LogFileSettings()
    test: LogTestSettings = LogTestSettings()

    opentelemetry: bool = False
    timestamp_format: str = "iso"
    logger_name: str = "app"
    log_level: LogLevel | None = None

    processor_override: list[Processor] | None = None
    propagated_loggers: list[str] | None = None
    cleared_loggers: list[str] | None = None

    def configure(self) -> None:
        if self.log_level:
            self.stream.log_level = self.log_level
            self.file.log_level = self.log_level
            self.test.log_level = self.log_level
        default_processors = self.get_default_processors()

        shared_processors: list[Processor] = (
            default_processors
            if self.processor_override is None
            else self.processor_override
        )

        structlog.configure(
            processors=shared_processors
            + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        self._setup_handlers(shared_processors)
        self._setup_cleared_loggers(self.cleared_loggers)
        self._setup_propagated_loggers(self.propagated_loggers)

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
        # if self.opentelemetry:
        #     default_processor_builder.add_opentelemetry()

        return default_processor_builder.get_processors()

    def get_logger(self):
        return get_logger(self.logger_name)

    def _setup_handlers(self, shared_processors: list[Processor]):
        handlers = []
        stream_handler = self.stream.handler(shared_processors)
        file_handler = self.file.handler(shared_processors)
        test_handler = self.test.handler(shared_processors)
        if stream_handler:
            handlers.append(stream_handler)
        if file_handler:
            handlers.append(file_handler)
        if test_handler:
            handlers.append(test_handler)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.NOTSET)
        root_logger.handlers = handlers

    def _setup_cleared_loggers(
        self,
        cleared_loggers: list[str] | None = None,
    ):
        default_cleared: list[str] = ["uvicorn.access"]
        if cleared_loggers is None:
            cleared_loggers = []
        cleared_loggers.extend(default_cleared)

        for _cleared_log in (
            cleared_loggers if cleared_loggers is not None else default_cleared
        ):
            # This prevents unwanted loggers from getting messages
            # through to begin with
            logging.getLogger(_cleared_log).handlers.clear()
            logging.getLogger(_cleared_log).propagate = False

    def _setup_propagated_loggers(
        self,
        propagated_loggers: list[str] | None = None,
    ):
        # Usually you do want these to be active in case something breaks
        default_propagated: list[str] = ["uvicorn", "uvicorn.error"]
        if propagated_loggers is None:
            propagated_loggers = []
        propagated_loggers.extend(default_propagated)

        for _propagated_log in (
            propagated_loggers
            if propagated_loggers is not None
            else default_propagated
        ):
            # This makes sure other loggers (third party) are handled
            # by structlog, not any other logger
            logging.getLogger(_propagated_log).handlers.clear()
            logging.getLogger(_propagated_log).propagate = True

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
