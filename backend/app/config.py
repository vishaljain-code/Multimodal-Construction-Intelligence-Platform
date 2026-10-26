from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    model: str = "claude-3-5-sonnet-20241022"
    cors_origins: str = "http://localhost:5173"
    max_image_mb: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
