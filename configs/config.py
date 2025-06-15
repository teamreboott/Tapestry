from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables.

    Unknown/unused environment variables are *ignored* so that secrets such as
    API keys can sit in `.env` without breaking validation.
    """

    APP_HOST: str = Field("0.0.0.0", env="APP_HOST")
    APP_PORT: int = Field(9004, env="APP_PORT")
    SEMAPHORE_LIMIT: int = Field(300, env="SEMAPHORE_LIMIT")
    DB_DIR: str = Field("mnt/nas/storage", env="DB_DIR")

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="openai_api_key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, alias="anthropic_api_key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="gemini_api_key")

    # Search
    SERPER_API_KEY: Optional[str] = Field(default=None, alias="serper_api_key")
    SERP_API_KEY: Optional[str] = Field(default=None, alias="serp_api_key")
    BRAVE_API_KEY: Optional[str] = Field(default=None, alias="brave_api_key")

    # PostgreSQL
    POSTGRES_USER: str = Field("askyourwork", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("admin", env="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field("localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field("webcrawldb", env="POSTGRES_DB")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str: # SQLAlchemy의 동기 엔진용 (테이블 생성 등)
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # allow unrelated secrets in .env