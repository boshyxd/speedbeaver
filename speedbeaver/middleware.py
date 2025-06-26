import time

import structlog
from asgi_correlation_id.context import correlation_id
from asgi_correlation_id.middleware import CorrelationIdMiddleware
from fastapi.applications import FastAPI
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp
from typing_extensions import Unpack

from speedbeaver.config import (
    LogSettings,
    LogSettingsArgs,
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


class StructlogMiddleware(BaseHTTPMiddleware):
    """
    TODO: Add docs
    """

    def __init__(
        self,
        app: ASGIApp,
        configure_logs: bool = True,
        **kwargs: Unpack[LogSettingsArgs],
    ):
        """
        Partial credit for this code goes to:
        - nymous (Link: https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e)
        - nkhitrov (Link: https://gist.github.com/nkhitrov/38adbb314f0d35371eba4ffb8f27078f)
        """

        super().__init__(app)

        if configure_logs:
            LogSettings(
                **kwargs
            ).configure()  # This just configures the logging automatically

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        structlog.contextvars.unbind_contextvars("request_id")
        request_id = correlation_id.get()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter_ns()
        default_error_message = (
            "Oops, we ran into a problem processing your request. "
            "Our team is working on fixing it!"
        )
        response = JSONResponse(
            content={
                "message": default_error_message,
                "request_id": request_id,
            },
            status_code=500,
        )
        try:
            response = await call_next(request)
        except Exception as e:
            if issubclass(type(e), KeyboardInterrupt):
                raise
            error_logger = structlog.stdlib.get_logger("speedbeaver.error")
            await error_logger.aexception("Uncaught exception")
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
            # Recreate the Uvicorn access log format,
            # but add all parameters as structured information
            logger = structlog.stdlib.get_logger("speedbeaver.access")
            await logger.ainfo(
                '%s:%s - "%s %s%s HTTP/%s" %s',
                client_host,
                client_port,
                http_method,
                url.path,
                f"?{url.query}" if url.query else "",
                http_version,
                status_code,
                http={
                    "url": str(url),
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


def quick_configure(
    app: FastAPI,
    **kwargs: Unpack[LogSettingsArgs],
):
    LogSettings(**kwargs).configure()
    app.add_middleware(StructlogMiddleware, **kwargs)
    app.add_middleware(CorrelationIdMiddleware)
