import os

os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("JSON_LOGS", "ON")
os.environ.setdefault("LOGGER_NAME", "env-var-app")

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from structlog_fastapi import StructlogMiddleware, get_logger

app = FastAPI()
app.add_middleware(StructlogMiddleware)
app.add_middleware(CorrelationIdMiddleware)

logger = get_logger()


@app.get("/")
async def index():
    await logger.info("I should be a secret!")
    await logger.warning("This should be the only thing you see!")
    return {"message": "Testing environment variables."}


if __name__ == "__main__":
    uvicorn.run(app)
