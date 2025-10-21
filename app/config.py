import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    TELEGRAM_BOT_TOKEN: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    FOOTBALL_SPORT_ID: int = 1
    LEAGUE_ID: int
    SEASON: int

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
        )


settings = Settings()
