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
    database_url: str
    sync_database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
