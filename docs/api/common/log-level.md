## Type Definition

```python
LogLevel = (
    Literal["DEBUG"]
    | Literal["INFO"]
    | Literal["WARNING"]
    | Literal["ERROR"]
    | Literal["CRITICAL"]
    | Literal["FATAL"]
)
```

## Log Level Reference

| Level    | Value        | Used For                                                                  |
| -------- | ------------ | ------------------------------------------------------------------------- |
| Debug    | `"DEBUG"`    | Detailed, debug-level information. Ideally, turn these off in production. |
| Info     | `"INFO"`     | Informational log messages, such as server startup or key events.         |
| Warning  | `"WARNING"`  |                                                                           |
| Error    | `"ERROR"`    |                                                                           |
| Critical | `"CRITICAL"` |                                                                           |
| Fatal    | `"FATAL"`    |                                                                           |

## Configuring Log Levels

TODO

### Quick Configure

TODO

### As Middleware

TODO

### Environment Variables

TODO
