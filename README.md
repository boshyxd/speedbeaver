# SpeedBeaver - Structlog Integration for FastAPI

When asked what their favourite part of a new project is, I can guarantee you very few developers will say this: **setting up logging.**

Thing is, logs are crucial for both security and development, giving you detailed insights as to what's going on at any given point with an application. They just . . . really suck to set up.

`SpeedBeaver` was built to have a simple, approachable, set-it-and-forget-it way of setting up logging middleware in FastAPI using `structlog`. It's designed as an alternative to the existing [`fastapi-structlog`](https://github.com/redb0/fastapi-logger).

## Current Status

The integration is currently in a pre-alpha state. API is subject to change, as is the name of the library itself, even. Heck, this thing isn't even on PyPI yet!

## Features

- 4 lines of config for the basics
- Optional BYOP (Bring Your Own Processors)
- Environment variable configuration via Pydantic Settings
- Async by default
- OpenTelemetry support (untested)

### Planned Features

- File logging
- Database integrations

## Installation

```bash
pip install speedbeaver
```

For OpenTelemetry support:

```bash
pip install speedbeaver[opentelemetry]
```

## Configuration

```python

```
