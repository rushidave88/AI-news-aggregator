

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # ── Groq
    groq_api_key: str

    # ── Email
    email_user: str
    email_password: str
    email_to: str

    # ── Database ─
    database_url: str = ""

    
    postgres_user: str     = "admin"
    postgres_password: str = "password"
    postgres_db: str       = "news_db"
    postgres_host: str     = "db"
    postgres_port: int     = 5432

    @property
    def db_url(self) -> str:
        """
        Returns the correct DB URL:
        - On Render  → uses DATABASE_URL env variable
        - Locally    → builds from individual params
        """
        if self.database_url:
            
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url

        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


settings = Settings()