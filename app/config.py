"""Application configuration via environment variables (12-Factor III)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration from environment variables. No hardcoded secrets."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "fastapi-crud-service"
    app_env: str = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (CP: PostgreSQL — consistency over availability under partition)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"

    # JWT Authentication
    jwt_secret_key: str = "CHANGE_ME_TO_A_RANDOM_SECRET_AT_LEAST_32_CHARS"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def database_url_sync(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "+psycopg2").replace(
            "+aiosqlite", ""
        )


settings = Settings()
