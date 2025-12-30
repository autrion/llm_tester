"""Ollama provider implementation (wrapper around existing client)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from llm_tester.client import OllamaClient as _OllamaClient
from llm_tester.client import OllamaError
from llm_tester.providers import LLMProvider, ProviderError

DEFAULT_BASE_URL = "http://localhost:11434"
BASE_URL_ENV = "OLLAMA_URL"


@dataclass
class OllamaProvider(LLMProvider):
    """Ollama provider (local models)."""

    base_url: str = DEFAULT_BASE_URL
    _client: _OllamaClient | None = None

    @classmethod
    def from_env(
        cls,
        *,
        timeout: int = 30,
        debug: bool = False,
        retries: int = 0,
        base_url: str | None = None,
    ) -> OllamaProvider:
        """Create provider from environment variables."""
        url = base_url or os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
        return cls(
            base_url=url,
            timeout=timeout,
            debug=debug,
            retries=retries,
        )

    def _get_client(self) -> _OllamaClient:
        """Lazy initialization of the Ollama client."""
        if self._client is None:
            self._client = _OllamaClient(
                base_url=self.base_url,
                timeout=self.timeout,
                debug=self.debug,
                retries=self.retries,
            )
        return self._client

    def generate(self, prompt: str, model: str, system: str | None = None) -> str:
        """Generate a response using Ollama."""
        client = self._get_client()
        try:
            return client.generate(prompt, model, system=system)
        except OllamaError as exc:
            raise ProviderError(str(exc)) from exc

    def estimate_cost(self, prompt: str, response: str, model: str) -> float:
        """Ollama is free (local inference)."""
        return 0.0


__all__ = ["OllamaProvider", "BASE_URL_ENV"]
