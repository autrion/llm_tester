"""OpenAI provider implementation."""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

from llm_tester.providers import LLMProvider, ProviderError

DEFAULT_BASE_URL = "https://api.openai.com/v1"
API_KEY_ENV = "OPENAI_API_KEY"

# Pricing per 1M tokens (USD) as of Dec 2025
PRICING = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "o1-preview": {"input": 15.0, "output": 60.0},
    "o1-mini": {"input": 3.0, "output": 12.0},
}


@dataclass
class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    api_key: str | None = None
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_env(
        cls,
        *,
        timeout: int = 30,
        debug: bool = False,
        retries: int = 0,
        base_url: str = DEFAULT_BASE_URL,
    ) -> OpenAIProvider:
        """Create provider from environment variables."""
        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise ProviderError(
                f"OpenAI API key not found. Set {API_KEY_ENV} environment variable."
            )
        return cls(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            debug=debug,
            retries=retries,
        )

    def _build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def generate(self, prompt: str, model: str, system: str | None = None) -> str:
        """Generate a response using OpenAI API."""
        if not self.api_key:
            raise ProviderError("OpenAI API key is not configured")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 1.0,
        }

        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._build_url(),
            data=encoded,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        attempts = max(self.retries, 0) + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                    if self.debug:
                        print(
                            f"OpenAI status: {getattr(response, 'status', 'unknown')}",
                            file=sys.stderr,
                        )
                    content = response.read().decode("utf-8")
                break
            except socket.timeout as exc:
                last_error = ProviderError(
                    "OpenAI request timed out. Increase the timeout or try again."
                )
                if attempt < attempts - 1:
                    if self.debug:
                        print(
                            f"Request timed out (attempt {attempt + 1}/{attempts}), retrying...",
                            file=sys.stderr,
                        )
                    continue
                raise last_error from exc
            except urllib.error.HTTPError as exc:
                message = exc.read().decode("utf-8")
                err = ProviderError(f"OpenAI returned HTTP {exc.code}: {message}")
                if attempt < attempts - 1 and exc.code >= 500:
                    last_error = err
                    if self.debug:
                        print(
                            f"HTTP {exc.code} from OpenAI (attempt {attempt + 1}/{attempts}), retrying...",
                            file=sys.stderr,
                        )
                    continue
                raise err from exc
            except urllib.error.URLError as exc:
                err = ProviderError(f"Could not reach OpenAI: {exc.reason}")
                raise err from exc

        if last_error and attempts > 1 and "content" not in locals():
            raise last_error

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError("Invalid JSON response from OpenAI") from exc

        return self._extract_message(payload)

    @staticmethod
    def _extract_message(payload: dict) -> str:
        """Extract the text message from OpenAI's response."""
        try:
            choices = payload.get("choices", [])
            if not choices:
                raise ProviderError("OpenAI response contained no choices")

            message = choices[0].get("message", {})
            content = message.get("content")

            if content is None:
                raise ProviderError("OpenAI response did not include message content")

            return str(content)
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected OpenAI response structure") from exc

    def estimate_cost(self, prompt: str, response: str, model: str) -> float:
        """Estimate cost based on token counts (rough approximation).

        Uses 4 characters ≈ 1 token heuristic.
        """
        # Normalize model name
        model_key = model
        for key in PRICING:
            if key in model.lower():
                model_key = key
                break

        if model_key not in PRICING:
            # Default to gpt-4o-mini pricing if unknown
            model_key = "gpt-4o-mini"

        pricing = PRICING[model_key]

        # Rough token estimation: ~4 chars per token
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        # Cost per million tokens
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


__all__ = ["OpenAIProvider", "API_KEY_ENV", "PRICING"]
