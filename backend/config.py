from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    llm_provider: str = "openrouter"

    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-chat"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    hf_home: str = str(BACKEND_DIR / ".cache" / "huggingface")
    knowledge_dir: Path = BACKEND_DIR.parent / "knowledge"

    embedding_model: str = "intfloat/multilingual-e5-small"
    chroma_dir: Path = BACKEND_DIR / "chroma_data"
    retrieval_k: int = 4

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
