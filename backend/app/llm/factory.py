from .base import LLMProvider
from ..config import settings

_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is not None:
        return _provider

    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "bedrock":
        from .bedrock_provider import BedrockProvider
        _provider = BedrockProvider()
    elif provider_name == "gemini":
        from .gemini_provider import GeminiProvider
        _provider = GeminiProvider()
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER={settings.LLM_PROVIDER!r}. "
            "Supported values: 'bedrock', 'gemini'."
        )

    return _provider
