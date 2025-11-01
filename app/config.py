from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    TELEGRAM_BOT_TOKEN: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    EXTERNAL_API_BASE_URL: str
    EXTERNAL_API_KEY: str
    EXTERNAL_API_SEASON: int

    MODE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
        )


settings = Settings()
