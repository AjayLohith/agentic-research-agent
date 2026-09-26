from typing import Optional
from app.providers.llm.base import LLMProvider
from app.providers.llm.groq import GroqProvider
from app.providers.llm.mock import MockLLMProvider


def get_llm_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: str = "llama-3.3-70b-versatile",
    base_url: str = "https://api.groq.com/openai/v1",
    mock_mode: bool = False
) -> LLMProvider:
    """Factory to instantiate the configured LLM provider."""
    if mock_mode or provider_name.lower() == "mock" or not api_key:
        return MockLLMProvider(model_name=model)

    if provider_name.lower() in ("groq", "openai"):
        return GroqProvider(api_key=api_key, model=model, base_url=base_url)

    return GroqProvider(api_key=api_key, model=model, base_url=base_url)


__all__ = [
    "LLMProvider",
    "GroqProvider",
    "MockLLMProvider",
    "get_llm_provider",
]
