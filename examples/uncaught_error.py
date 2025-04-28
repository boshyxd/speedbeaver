import uvicorn
from fastapi import FastAPI

import speedbeaver

app = FastAPI()
speedbeaver.quick_configure(app, log_level="DEBUG")

logger = speedbeaver.get_logger()


@app.get("/")
async def force_error():
    raise NotImplementedError


if __name__ == "__main__":
    uvicorn.run(app)
