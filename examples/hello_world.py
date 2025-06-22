import uvicorn
from fastapi import FastAPI

import speedbeaver
from speedbeaver.handlers import LogTestSettings

app = FastAPI()

# Note: The test settings are mostly for our integration tests
speedbeaver.quick_configure(
    app,
    test=LogTestSettings(file_name="hello_world.test.log"),
)

logger = speedbeaver.get_logger()


@app.get("/")
async def index():
    await logger.ainfo("Hello, world!")
    return {"message": "Hello, world!"}


if __name__ == "__main__":
    uvicorn.run(app)
