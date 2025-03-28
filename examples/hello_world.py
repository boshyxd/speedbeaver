import logging

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from structlog_fastapi import StructlogMiddleware, get_logger

app = FastAPI()
app.add_middleware(StructlogMiddleware, log_level=logging.DEBUG)
app.add_middleware(CorrelationIdMiddleware)

logger = get_logger()


@app.get("/")
async def index():
    await logger.info("Hello, world!")
    return {"message": "Hello, world!"}


if __name__ == "__main__":
    uvicorn.run(app)
