"""Multi-provider abstraction for LLM APIs."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ProviderError(RuntimeError):
    """Raised when an LLM provider returns an error or unexpected payload."""


@dataclass
class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    timeout: int = 30
    debug: bool = False
    retries: int = 0

    @abstractmethod
    def generate(self, prompt: str, model: str, system: str | None = None) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt to send to the model
            model: The model identifier
            system: Optional system prompt

        Returns:
            The generated text response

        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    def estimate_cost(self, prompt: str, response: str, model: str) -> float:
        """Estimate the cost of a request in USD.

        Args:
            prompt: The input prompt
            response: The generated response
            model: The model identifier

        Returns:
            Estimated cost in USD
        """
        pass

    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic')."""
        return self.__class__.__name__.lower().replace("provider", "")


__all__ = ["LLMProvider", "ProviderError"]
