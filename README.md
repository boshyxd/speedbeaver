# SpeedBeaver - Structlog Integration for FastAPI

When asked what their favourite part of a new project is, I can guarantee you very few developers will say this: **setting up logging.**

Thing is, logs are crucial for both security and development, giving you detailed insights as to what's going on at any given point with an application. They just . . . really suck to set up.

SpeedBeaver was built to have a simple, approachable, set-it-and-forget-it way of setting up logging middleware in FastAPI using `structlog`. It's designed as an alternative to the existing [`fastapi-structlog`](https://github.com/redb0/fastapi-logger).

## Current Status

The integration is currently in a pre-alpha state. API is subject to change, as is the name of the library itself, even.

## Features

- 3-4 lines of config for the basics
- Optional BYOP (Bring Your Own Processors)
- Environment variable configuration via Pydantic Settings
- File logging

### Planned Features

- OpenTelemetry integrations
- Database integrations

## Installation

> [!CAUTION]
> SpeedBeaver is NOT yet on PyPI! The below command(s) will not work until this README is updated and the project is fully released.

```bash
pip install speedbeaver
```

## Configuration

To drop SpeedBeaver into any async FastAPI app, see the following Python snippet:

```python
from fastapi import FastAPI

import speedbeaver

app = FastAPI()
speedbeaver.quick_configure(app)

# Try using the line below instead to see the difference!
# speedbeaver.quick_configure(app, log_level="DEBUG")

logger = speedbeaver.get_logger()


@app.get("/")
async def index():
    await logger.debug("I'm a debug message!")
    await logger.info("Hello, world!")
    return {"message": "Hello, world!"}
```
