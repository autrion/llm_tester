"""Azure OpenAI provider implementation."""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

from llm_tester.providers import LLMProvider, ProviderError

API_KEY_ENV = "AZURE_OPENAI_API_KEY"
ENDPOINT_ENV = "AZURE_OPENAI_ENDPOINT"
DEPLOYMENT_ENV = "AZURE_OPENAI_DEPLOYMENT"
API_VERSION = "2024-02-15-preview"

# Azure pricing is same as OpenAI, but billed differently
# Pricing per 1M tokens (USD) - depends on deployment type
PRICING = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-35-turbo": {"input": 0.5, "output": 1.5},
}


@dataclass
class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI API provider."""

    api_key: str | None = None
    endpoint: str | None = None
    deployment: str | None = None
    api_version: str = API_VERSION

    @classmethod
    def from_env(
        cls,
        *,
        timeout: int = 30,
        debug: bool = False,
        retries: int = 0,
    ) -> AzureOpenAIProvider:
        """Create provider from environment variables."""
        api_key = os.environ.get(API_KEY_ENV)
        endpoint = os.environ.get(ENDPOINT_ENV)
        deployment = os.environ.get(DEPLOYMENT_ENV)

        if not api_key:
            raise ProviderError(
                f"Azure OpenAI API key not found. Set {API_KEY_ENV} environment variable."
            )
        if not endpoint:
            raise ProviderError(
                f"Azure OpenAI endpoint not found. Set {ENDPOINT_ENV} environment variable."
            )

        return cls(
            api_key=api_key,
            endpoint=endpoint,
            deployment=deployment,
            timeout=timeout,
            debug=debug,
            retries=retries,
        )

    def _build_url(self, deployment: str) -> str:
        """Build Azure OpenAI API URL."""
        if not self.endpoint:
            raise ProviderError("Azure endpoint is not configured")

        endpoint = self.endpoint.rstrip("/")
        return f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={self.api_version}"

    def generate(self, prompt: str, model: str, system: str | None = None) -> str:
        """Generate a response using Azure OpenAI API.

        Args:
            prompt: User prompt
            model: Deployment name (or uses AZURE_OPENAI_DEPLOYMENT env var)
            system: Optional system prompt
        """
        if not self.api_key:
            raise ProviderError("Azure OpenAI API key is not configured")

        # Use provided model as deployment name, or fall back to env var
        deployment = model or self.deployment
        if not deployment:
            raise ProviderError(
                f"Azure deployment name not specified. Set {DEPLOYMENT_ENV} or pass model parameter."
            )

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "temperature": 1.0,
        }

        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._build_url(deployment),
            data=encoded,
            headers={
                "Content-Type": "application/json",
                "api-key": self.api_key,
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
                            f"Azure OpenAI status: {getattr(response, 'status', 'unknown')}",
                            file=sys.stderr,
                        )
                    content = response.read().decode("utf-8")
                break
            except socket.timeout as exc:
                last_error = ProviderError(
                    "Azure OpenAI request timed out. Increase the timeout or try again."
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
                err = ProviderError(f"Azure OpenAI returned HTTP {exc.code}: {message}")
                if attempt < attempts - 1 and exc.code >= 500:
                    last_error = err
                    if self.debug:
                        print(
                            f"HTTP {exc.code} from Azure (attempt {attempt + 1}/{attempts}), retrying...",
                            file=sys.stderr,
                        )
                    continue
                raise err from exc
            except urllib.error.URLError as exc:
                err = ProviderError(f"Could not reach Azure OpenAI: {exc.reason}")
                raise err from exc

        if last_error and attempts > 1 and "content" not in locals():
            raise last_error

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError("Invalid JSON response from Azure OpenAI") from exc

        return self._extract_message(payload)

    @staticmethod
    def _extract_message(payload: dict) -> str:
        """Extract the text message from Azure OpenAI's response (same format as OpenAI)."""
        try:
            choices = payload.get("choices", [])
            if not choices:
                raise ProviderError("Azure OpenAI response contained no choices")

            message = choices[0].get("message", {})
            content = message.get("content")

            if content is None:
                raise ProviderError("Azure OpenAI response did not include message content")

            return str(content)
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected Azure OpenAI response structure") from exc

    def estimate_cost(self, prompt: str, response: str, model: str) -> float:
        """Estimate cost based on token counts (rough approximation).

        Uses 4 characters ≈ 1 token heuristic.
        Note: Azure pricing varies by region and commitment tier.
        """
        # Normalize model/deployment name
        model_key = "gpt-35-turbo"  # default
        for key in PRICING:
            if key in model.lower():
                model_key = key
                break

        pricing = PRICING[model_key]

        # Rough token estimation: ~4 chars per token
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        # Cost per million tokens
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


__all__ = ["AzureOpenAIProvider", "API_KEY_ENV", "ENDPOINT_ENV", "DEPLOYMENT_ENV", "PRICING"]
