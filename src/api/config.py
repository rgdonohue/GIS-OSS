from functools import lru_cache

from pydantic import AliasChoices, ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GIS-OSS API"
    api_key: str = Field(default="")
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT", "environment"),
    )
    db_host: str = Field(default="localhost", validation_alias=AliasChoices("POSTGRES_HOST", "db_host"))
    db_port: int = Field(default=5432, validation_alias=AliasChoices("POSTGRES_PORT", "db_port"))
    db_name: str = Field(default="gis_oss", validation_alias=AliasChoices("POSTGRES_DB", "db_name"))
    db_user: str = Field(default="gis_user", validation_alias=AliasChoices("POSTGRES_USER", "db_user"))
    db_password: str = Field(default="changeme", validation_alias=AliasChoices("POSTGRES_PASSWORD", "db_password"))
    db_pool_min: int = Field(default=1)
    db_pool_max: int = Field(default=5)
    log_level: str = Field(default="INFO")
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=60)
    rate_limit_window_seconds: int = Field(default=60)


@lru_cache
def get_settings() -> Settings:
    return Settings()
