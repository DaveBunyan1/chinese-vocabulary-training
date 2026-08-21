from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = (
        "postgresql+asyncpg://chinese:chinese@localhost:5432/chinese_learning"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
