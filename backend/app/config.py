from typing import List, ClassVar
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # load the .env file relative to this config module so it's independent of CWD
    env_path: ClassVar[Path] = Path(__file__).resolve().parents[1] / ".env"
    model_config = SettingsConfigDict(env_file=str(env_path), extra="ignore")

    DATABASE_URL: str = "mysql+pymysql://root:Dhruv#1620@localhost:3306/yelp_db?charset=utf8mb4"
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]
    YELP_API_KEY: str | None = "hVcNORP2ai_e6cOuKUj_sk2z3eyXSV700ohaSyXx69O-0J6bubAOv6f3ZP0Qdw_7wzx98lvjGSBadzhvm3UnToURsgtkoNykcc0Tk66x0Hyoq9W6S1GJXD27X46_aXYx"
    OLLAMA_URL: str | None = None
    OLLAMA_MODEL: str | None = None
    TAVILY_URL: str | None = None
    TAVILY_API_KEY: str | None = None


settings = Settings()