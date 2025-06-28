# Log Levels

## Log Level Reference

| Level    | Value        | Used For                                                                  |
| -------- | ------------ | ------------------------------------------------------------------------- |
| Debug    | `"DEBUG"`    | Detailed, debug-level information. Ideally, turn these off in production. |
| Info     | `"INFO"`     | Informational log messages, such as server startup or key events.         |
| Warning  | `"WARNING"`  | Something has gone kinda wonky, like a failed login attempt.              |
| Error    | `"ERROR"`    | Something has gone wrong, like a failed response from a third party API.  |
| Critical | `"CRITICAL"` | Something has gone _really_ wrong, like a database not responding.        |
| Fatal    | `"FATAL"`    | Something has gone so catastrophically wrong the app has to shut down.    |

## Configuring Log Levels

### Quick Configure

This example sets the log level of the entire application to Debug.

```python
from fastapi import FastAPI

from speedbeaver import quick_configure

app = FastAPI()

quick_configure(app, log_level="DEBUG")
```

### As Middleware

This is useful if you need some more control over how your application's middleware and/or logging is laid out. The example below sets the log level to Info for the entire app.

```python
from asgi_correlation_id.middleware import CorrelationIdMiddleware
from fastapi import FastAPI

from speedbeaver import StructlogMiddleware

app = FastAPI()

app.add_middleware(StructlogMiddleware, log_level="INFO")
app.add_middleware(CorrelationIdMiddleware)
```

### Per-Handler

The example below sets the log level to Warning for the stream handler and to Debug for the file handler. This lets you see all log messages in the file while keeping stream handlers relatively clutter-free.

```python
from fastapi import FastAPI

from speedbeaver import quick_configure
from speedbeaver.handlers import (
    LogFileSettings,
    LogStreamSettings,
)

app = FastAPI()

quick_configure(
    app,
    stream=LogStreamSettings(log_level="WARNING"),
    file=LogFileSettings(log_level="DEBUG", enabled=True, file_name="app.log"),
)
```

### Environment Variables

You can use your environment variables to configure your log levels, either per handler or overall.

An overall setting would look like this:

```bash
# .env
LOG_LEVEL=DEBUG
```

While a per-handler setting would look like this:

```bash
# .env
STREAM__LOG_LEVEL=WARNING
FILE__LOG_LEVEL=DEBUG
FILE__ENABLED=True # Don't forget to enable the handler!
```
