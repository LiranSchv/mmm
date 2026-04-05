from __future__ import annotations
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mmm.db"
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"


settings = Settings()
