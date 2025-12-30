"""Anthropic provider implementation."""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

from llm_tester.providers import LLMProvider, ProviderError

DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_VERSION = "2023-06-01"

# Pricing per 1M tokens (USD) as of Dec 2025
PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


@dataclass
class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

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
    ) -> AnthropicProvider:
        """Create provider from environment variables."""
        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise ProviderError(
                f"Anthropic API key not found. Set {API_KEY_ENV} environment variable."
            )
        return cls(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            debug=debug,
            retries=retries,
        )

    def _build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/messages"

    def generate(self, prompt: str, model: str, system: str | None = None) -> str:
        """Generate a response using Anthropic API."""
        if not self.api_key:
            raise ProviderError("Anthropic API key is not configured")

        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            payload["system"] = system

        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._build_url(),
            data=encoded,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_VERSION,
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
                            f"Anthropic status: {getattr(response, 'status', 'unknown')}",
                            file=sys.stderr,
                        )
                    content = response.read().decode("utf-8")
                break
            except socket.timeout as exc:
                last_error = ProviderError(
                    "Anthropic request timed out. Increase the timeout or try again."
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
                err = ProviderError(f"Anthropic returned HTTP {exc.code}: {message}")
                if attempt < attempts - 1 and exc.code >= 500:
                    last_error = err
                    if self.debug:
                        print(
                            f"HTTP {exc.code} from Anthropic (attempt {attempt + 1}/{attempts}), retrying...",
                            file=sys.stderr,
                        )
                    continue
                raise err from exc
            except urllib.error.URLError as exc:
                err = ProviderError(f"Could not reach Anthropic: {exc.reason}")
                raise err from exc

        if last_error and attempts > 1 and "content" not in locals():
            raise last_error

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError("Invalid JSON response from Anthropic") from exc

        return self._extract_message(payload)

    @staticmethod
    def _extract_message(payload: dict) -> str:
        """Extract the text message from Anthropic's response."""
        try:
            content_blocks = payload.get("content", [])
            if not content_blocks:
                raise ProviderError("Anthropic response contained no content")

            # Get the first text block
            for block in content_blocks:
                if block.get("type") == "text":
                    text = block.get("text")
                    if text is not None:
                        return str(text)

            raise ProviderError("Anthropic response did not include text content")
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected Anthropic response structure") from exc

    def estimate_cost(self, prompt: str, response: str, model: str) -> float:
        """Estimate cost based on token counts (rough approximation).

        Uses 4 characters ≈ 1 token heuristic.
        """
        # Normalize model name
        model_key = model
        if model_key not in PRICING:
            # Try to find a matching key
            for key in PRICING:
                if key in model.lower() or model.lower() in key:
                    model_key = key
                    break
            else:
                # Default to Claude 3.5 Haiku pricing if unknown (cheapest)
                model_key = "claude-3-5-haiku-20241022"

        pricing = PRICING[model_key]

        # Rough token estimation: ~4 chars per token
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        # Cost per million tokens
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


__all__ = ["AnthropicProvider", "API_KEY_ENV", "PRICING", "ANTHROPIC_VERSION"]
