import uvicorn
from fastapi import FastAPI

import speedbeaver

app = FastAPI()
speedbeaver.quick_configure(app)

logger = speedbeaver.get_logger()


@app.get("/")
async def index():
    await logger.ainfo("Hello, world!")
    return {"message": "Hello, world!"}


if __name__ == "__main__":
    uvicorn.run(app)
