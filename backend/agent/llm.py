import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from config import get_settings

logger = logging.getLogger(__name__)


def get_llm() -> BaseChatModel:
    settings = get_settings()
    temperature_kwargs = {} if settings.llm_temperature is None else {"temperature": settings.llm_temperature}

    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in backend/.env")
        logger.info("llm: using anthropic provider, model=%s", settings.anthropic_model)
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout_s,
            max_retries=settings.llm_max_retries,
            **temperature_kwargs,
        )

    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in backend/.env")
    logger.info("llm: using openrouter provider, model=%s", settings.openrouter_model)
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        timeout=settings.llm_timeout_s,
        max_retries=settings.llm_max_retries,
        **temperature_kwargs,
    )
