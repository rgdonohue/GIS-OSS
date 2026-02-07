from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GIS-OSS API"
    api_key: str = Field(default="")
    db_read_dsn: str = Field(
        default="",
        validation_alias=AliasChoices(
            "READONLY_DATABASE_URL",
            "POSTGRES_READONLY_DSN",
            "db_read_dsn",
        ),
    )
    db_dsn: str = Field(
        default="",
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_DSN", "db_dsn"),
    )
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT", "environment"),
    )
    db_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("POSTGRES_HOST", "db_host"),
    )
    db_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("POSTGRES_PORT", "db_port"),
    )
    db_name: str = Field(
        default="gis_oss",
        validation_alias=AliasChoices("POSTGRES_DB", "db_name"),
    )
    db_user: str = Field(
        default="gis_user",
        validation_alias=AliasChoices("POSTGRES_USER", "db_user"),
    )
    db_password: str = Field(
        default="changeme",
        validation_alias=AliasChoices("POSTGRES_PASSWORD", "db_password"),
    )
    db_read_user: str = Field(
        default="",
        validation_alias=AliasChoices("POSTGRES_READONLY_USER", "db_read_user"),
    )
    db_read_password: str = Field(
        default="",
        validation_alias=AliasChoices(
            "POSTGRES_READONLY_PASSWORD",
            "db_read_password",
        ),
    )
    db_pool_min: int = Field(default=1)
    db_pool_max: int = Field(default=5)
    log_level: str = Field(default="INFO")
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=60)
    rate_limit_window_seconds: int = Field(default=60)
    rate_limit_max_identifiers: int = Field(default=10_000)
    rate_limit_bucket_ttl_seconds: int = Field(default=3_600)
    authz_backend: str = Field(
        default="database",
        validation_alias=AliasChoices("AUTHZ_BACKEND", "authz_backend"),
    )
    allow_public_api: bool = Field(
        default=False,
        validation_alias=AliasChoices("ALLOW_PUBLIC_API", "allow_public_api"),
    )
    otel_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_OTEL", "otel_enabled"),
    )
    otel_service_name: str = Field(
        default="gis-oss-api",
        validation_alias=AliasChoices("OTEL_SERVICE_NAME", "otel_service_name"),
    )
    enable_audit_log: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_AUDIT_LOG", "enable_audit_log"),
    )
    allowed_query_tables: str = Field(
        default="data.features",
        validation_alias=AliasChoices("ALLOWED_QUERY_TABLES", "allowed_query_tables"),
    )
    enable_local_llm_planner: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "ENABLE_LOCAL_LLM_PLANNER",
            "enable_local_llm_planner",
        ),
    )
    llm_provider: str = Field(
        default="ollama",
        validation_alias=AliasChoices("LLM_PROVIDER", "llm_provider"),
    )
    llm_ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("LLM_OLLAMA_BASE_URL", "llm_ollama_base_url"),
    )
    llm_model: str = Field(
        default="qwen2.5:7b-instruct",
        validation_alias=AliasChoices("LLM_MODEL", "llm_model"),
    )
    llm_timeout_seconds: float = Field(
        default=20,
        validation_alias=AliasChoices("LLM_TIMEOUT_SECONDS", "llm_timeout_seconds"),
    )
    llm_max_retries: int = Field(
        default=1,
        validation_alias=AliasChoices("LLM_MAX_RETRIES", "llm_max_retries"),
    )
    llm_prompt_max_chars: int = Field(
        default=4000,
        validation_alias=AliasChoices("LLM_PROMPT_MAX_CHARS", "llm_prompt_max_chars"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
