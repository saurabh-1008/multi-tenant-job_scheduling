from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str
    # Redis / broker
    redis_url: str
    # JWT auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    # App metadata
    app_name: str = "Multi-Tenant Workflow Engine"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """
    Cached so we parse the .env file once, not on every request.
    Import this function anywhere you need config — never import
    Settings() directly.
    """
    return Settings()