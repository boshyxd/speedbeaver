from typing import Literal

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

OnOrOff = Literal["ON"] | Literal["OFF"]

LogLevel = (
    Literal["DEBUG"]
    | Literal["INFO"]
    | Literal["WARNING"]
    | Literal["ERROR"]
    | Literal["CRITICAL"]
    | Literal["FATAL"]
)


class LogSettingsDefaults:
    JSON_LOGS: bool = False
    OPENTELEMETRY: bool = False
    LOG_LEVEL: LogLevel = "INFO"
    TIMESTAMP_FORMAT: str = "iso"
    LOGGER_NAME: str = "app"

    TEST_MODE: bool = False
    LOG_FILE_NAME: str | None = None


class LogSettings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True)

    JSON_LOGS: bool
    OPENTELEMETRY: bool
    LOG_LEVEL: LogLevel
    TIMESTAMP_FORMAT: str
    LOGGER_NAME: str

    TEST_MODE: bool
    LOG_FILE_NAME: str | None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return super().settings_customise_sources(
            settings_cls,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            init_settings,
        )
