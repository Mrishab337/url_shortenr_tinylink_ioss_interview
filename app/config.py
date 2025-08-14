from pydantic_settings import BaseSettings
from pydantic import AnyUrl
from typing import Optional

class Settings(BaseSettings):
    APP_BASE_URL: str = "http://127.0.0.1:8000"
    DATABASE_URL: str = "sqlite:///data/urls.db"
    CODE_LENGTH: int = 6

    class Config:
        env_file = ".env"

settings = Settings()
