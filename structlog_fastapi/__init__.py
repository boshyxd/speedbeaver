import structlog

from structlog_fastapi.middleware import StructlogMiddleware
from structlog_fastapi.processor_collection_builder import (
    ProcessorCollectionBuilder,
)


def get_logger(name: str = "app") -> structlog.stdlib.AsyncBoundLogger:
    return structlog.get_logger(name)


__all__ = ["StructlogMiddleware", "ProcessorCollectionBuilder"]
