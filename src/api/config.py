from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "GIS-OSS API"
    api_key: str = Field(default="", env="API_KEY")
    environment: str = Field(default="development", env="APP_ENV")
    db_host: str = Field(default="localhost", env="POSTGRES_HOST")
    db_port: int = Field(default=5432, env="POSTGRES_PORT")
    db_name: str = Field(default="gis_oss", env="POSTGRES_DB")
    db_user: str = Field(default="gis_user", env="POSTGRES_USER")
    db_password: str = Field(default="changeme", env="POSTGRES_PASSWORD")
    db_pool_min: int = Field(default=1, env="DB_POOL_MIN")
    db_pool_max: int = Field(default=5, env="DB_POOL_MAX")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=60, env="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(
        default=60, env="RATE_LIMIT_WINDOW_SECONDS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
