from __future__ import annotations
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/mmm_platform"
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"


settings = Settings()
