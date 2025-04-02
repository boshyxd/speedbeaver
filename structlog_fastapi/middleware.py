import logging
import sys
import time

import structlog
from asgi_correlation_id.context import correlation_id
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from structlog.types import Processor

from structlog_fastapi.config import LogLevel, settings
from structlog_fastapi.processor_collection_builder import (
    ProcessorCollectionBuilder,
)


class StructlogMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        json_logs: bool = settings.JSON_LOGS,
        log_level: LogLevel = settings.LOG_LEVEL,
        timestamp_format: str = settings.TIMESTAMP_FORMAT,
        processor_override: list[Processor] | None = None,
        propagated_loggers: list[str] | None = None,
        cleared_loggers: list[str] | None = None,
    ):
        """
        Partial credit for this code goes to:
        - nymous (Link: https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e)
        - nkhitrov (Link: https://gist.github.com/nkhitrov/38adbb314f0d35371eba4ffb8f27078f)
        """
        super().__init__(app)

        default_processors = self.get_default_processors(
            timestamp_format, json_logs
        )
        shared_processors: list[Processor] = (
            default_processors
            if processor_override is None
            else processor_override
        )

        structlog.configure(
            processors=shared_processors
            + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.AsyncBoundLogger,
            cache_logger_on_first_use=True,
        )

        self.root_logger = logging.getLogger()

        self._setup_handler(shared_processors, log_level, json_logs)
        self._setup_propagated_loggers(propagated_loggers)
        self._setup_cleared_loggers(cleared_loggers)

        sys.excepthook = self.handle_exception

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = correlation_id.get()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter_ns()
        response = Response(status_code=500)
        try:
            response = await call_next(request)
        except Exception as e:
            await structlog.get_logger("structlog_fastapi.error").error(
                "Uncaught exception",
                exc_info=(e),
            )
            raise
        finally:
            process_time = time.perf_counter_ns() - start_time
            status_code = response.status_code
            url = request.url
            client_host = "unknown"
            client_port = 0
            if request.client:
                client_host = request.client.host
                client_port = request.client.port
            http_method = request.method
            http_version = request.scope["http_version"]
            # Recreate the Uvicorn access log format, but add all parameters as structured information
            await structlog.get_logger("structlog_fastapi.access").info(
                '%s:%s - "%s %s%s HTTP/%s" %s',
                client_host,
                client_port,
                http_method,
                url.path,
                f"?{url.query}" if url.query else "",
                http_version,
                status_code,
                http={
                    "url": url,
                    "status_code": status_code,
                    "method": http_method,
                    "request_id": request_id,
                    "version": http_version,
                },
                network={"client": {"ip": client_host, "port": client_port}},
                duration=process_time,
            )
            response.headers["X-Process-Time"] = str(process_time / 10**9)
        return response

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        self.root_logger.getChild("structlog_fastapi.error").error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    @classmethod
    def get_default_processors(
        cls, timestamp_format: str = "iso", json_logs: bool = False
    ) -> list[Processor]:
        default_processor_builder = (
            ProcessorCollectionBuilder()
            .add_log_level()
            .add_logger_name()
            .add_positional_arguments()
            .add_callsite_parameters()
            .add_timestamp(format=timestamp_format)
            .add_stack_info_renderer()
        )
        if json_logs:
            default_processor_builder.add_exception_info()
        return default_processor_builder.get_processors()

    def _setup_handler(
        self,
        shared_processors: list[Processor],
        log_level: LogLevel = settings.LOG_LEVEL,
        json_logs: bool = False,
    ):
        log_renderer: structlog.types.Processor
        if json_logs:
            log_renderer = structlog.processors.JSONRenderer()
        else:
            log_renderer = structlog.dev.ConsoleRenderer()

        formatter = structlog.stdlib.ProcessorFormatter(
            # These run ONLY on `logging` entries that do NOT originate within
            # structlog.
            foreign_pre_chain=shared_processors,
            # These run on ALL entries after the pre_chain is done.
            processors=[
                # Remove _record & _from_structlog.
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                log_renderer,
            ],
        )

        handler = logging.StreamHandler()
        # This lets our processors handle all logging requests.
        handler.setFormatter(formatter)
        self.root_logger.addHandler(handler)
        self.root_logger.setLevel(log_level.value)

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
