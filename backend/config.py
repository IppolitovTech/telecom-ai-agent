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

    # Per-attempt cap on each LLM request (classification/react-step/synthesis).
    # Free OpenRouter models occasionally stall under load; without this the
    # SDK's own default (minutes) leaves the request hanging well past the
    # point the frontend has already given up and shown its own error.
    llm_timeout_s: float = 15.0
    # The SDK retries a timed-out request by default (2 retries = 3 attempts),
    # and each retry waits the *full* timeout again — 3x llm_timeout_s in the
    # worst case. One retry keeps a single stalled call bounded to ~2x llm_timeout_s.
    llm_max_retries: int = 1

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
