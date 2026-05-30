from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    paddle_secret_key: str
    paddle_api_key: str
    paddle_api_base: str = "https://api.paddle.com"
    database_url: str
    sync_database_url: str
    license_secret_key: str
    paddle_env: str = "production"
    log_level: str = "INFO"
    db_echo: bool = False
    resend_api_key: str
    email_from: str


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
