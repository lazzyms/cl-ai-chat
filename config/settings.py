import json

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os

load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/mydb"
    )

    serper_api_key: str = os.getenv("SERPER_API_KEY", "")

    files: str = os.getenv("FILES", "[]")

    model: str = os.getenv("OLLAMA_MODEL", "gpt-3.5-turbo")

    @property
    def file_ids(self) -> list[int]:
        try:
            return json.loads(self.files) if self.files else []
        except json.JSONDecodeError:
            return []


settings = Settings()
