from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Adaptive English Communication Coach"
    database_url: str = "sqlite:///./coach.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "development-secret-change-me-please"
    access_token_minutes: int = 60 * 24
    openai_api_key: str | None = None
    cors_origins: str = "http://localhost:3000"


settings = Settings()
