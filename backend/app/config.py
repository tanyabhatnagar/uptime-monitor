import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database connection URL (e.g. postgresql+asyncpg://...)
    DATABASE_URL: str

    # Execution environment (development, production)
    ENV: str = "development"

    # Configuration to load from .env file
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Instantiate settings to be imported across the application
settings = Settings()
