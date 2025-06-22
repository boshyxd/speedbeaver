import uvicorn
from fastapi import FastAPI

import speedbeaver
from speedbeaver.handlers import LogTestSettings

app = FastAPI()
# Note: The test settings are mostly for our integration tests
speedbeaver.quick_configure(
    app,
    log_level="DEBUG",
    test=LogTestSettings(file_name="uncaught_error.test.log"),
)

logger = speedbeaver.get_logger()


@app.get("/")
async def force_error():
    raise NotImplementedError


if __name__ == "__main__":
    uvicorn.run(app)
