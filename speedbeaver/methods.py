import structlog


def get_logger(
    name: str = "app",
) -> structlog.stdlib.BoundLogger:
    return structlog.stdlib.get_logger(name)
