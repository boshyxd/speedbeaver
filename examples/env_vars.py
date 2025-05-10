import os

os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("JSON_LOGS", "YES")
os.environ.setdefault("LOGGER_NAME", "env-var-app")

import uvicorn
from fastapi import FastAPI

import speedbeaver

app = FastAPI()
speedbeaver.quick_configure(app)

logger = speedbeaver.get_logger()


@app.get("/")
async def index():
    await logger.info("I should be a secret!")
    await logger.warning("This should be the only thing you see!")
    return {"message": "Testing environment variables."}


if __name__ == "__main__":
    uvicorn.run(app)
