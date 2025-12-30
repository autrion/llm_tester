"""Provider factory for creating LLM providers."""
from __future__ import annotations

from typing import Literal

from llm_tester.providers import LLMProvider, ProviderError
from llm_tester.providers.anthropic import AnthropicProvider
from llm_tester.providers.azure import AzureOpenAIProvider
from llm_tester.providers.google import GoogleProvider
from llm_tester.providers.ollama import OllamaProvider
from llm_tester.providers.openai import OpenAIProvider

ProviderType = Literal["openai", "anthropic", "google", "azure", "ollama"]

PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "azure": AzureOpenAIProvider,
    "ollama": OllamaProvider,
}


def create_provider(
    provider: ProviderType,
    *,
    timeout: int = 30,
    debug: bool = False,
    retries: int = 0,
    **kwargs,
) -> LLMProvider:
    """Create a provider instance from environment variables.

    Args:
        provider: Provider type (openai, anthropic, google, azure, ollama)
        timeout: Request timeout in seconds
        debug: Enable debug output
        retries: Number of retries for transient errors
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured provider instance

    Raises:
        ProviderError: If provider is unknown or configuration is invalid
    """
    if provider not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ProviderError(
            f"Unknown provider: {provider}. Available providers: {available}"
        )

    provider_class = PROVIDERS[provider]
    return provider_class.from_env(timeout=timeout, debug=debug, retries=retries, **kwargs)


def list_providers() -> list[str]:
    """Return list of available provider names."""
    return list(PROVIDERS.keys())


__all__ = ["create_provider", "list_providers", "ProviderType", "PROVIDERS"]
