from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Adaptive English Communication Coach"
    app_env: str = "development"
    database_url: str = "sqlite:///./coach.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "development-secret-change-me-please"
    access_token_minutes: int = 60 * 24
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"

    @model_validator(mode="after")
    def production_secrets(self):
        if self.app_env.lower() == "production" and (len(self.secret_key) < 32 or self.secret_key == "development-secret-change-me-please"):
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return self


settings = Settings()
