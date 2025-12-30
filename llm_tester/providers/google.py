"""Google (Gemini) provider implementation."""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

from llm_tester.providers import LLMProvider, ProviderError

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
API_KEY_ENV = "GOOGLE_API_KEY"

# Pricing per 1M tokens (USD) as of Dec 2025
PRICING = {
    "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free during preview
    "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
    "gemini-1.0-pro": {"input": 0.5, "output": 1.5},
}


@dataclass
class GoogleProvider(LLMProvider):
    """Google Gemini API provider."""

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
    ) -> GoogleProvider:
        """Create provider from environment variables."""
        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise ProviderError(
                f"Google API key not found. Set {API_KEY_ENV} environment variable."
            )
        return cls(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            debug=debug,
            retries=retries,
        )

    def _build_url(self, model: str) -> str:
        return f"{self.base_url.rstrip('/')}/models/{model}:generateContent?key={self.api_key}"

    def generate(self, prompt: str, model: str, system: str | None = None) -> str:
        """Generate a response using Google Gemini API."""
        if not self.api_key:
            raise ProviderError("Google API key is not configured")

        # Build contents
        contents = []

        # Add system instruction if provided
        system_instruction = None
        if system:
            system_instruction = {"parts": [{"text": system}]}

        # Add user message
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._build_url(model),
            data=encoded,
            headers={
                "Content-Type": "application/json",
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
                            f"Google status: {getattr(response, 'status', 'unknown')}",
                            file=sys.stderr,
                        )
                    content = response.read().decode("utf-8")
                break
            except socket.timeout as exc:
                last_error = ProviderError(
                    "Google request timed out. Increase the timeout or try again."
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
                err = ProviderError(f"Google returned HTTP {exc.code}: {message}")
                if attempt < attempts - 1 and exc.code >= 500:
                    last_error = err
                    if self.debug:
                        print(
                            f"HTTP {exc.code} from Google (attempt {attempt + 1}/{attempts}), retrying...",
                            file=sys.stderr,
                        )
                    continue
                raise err from exc
            except urllib.error.URLError as exc:
                err = ProviderError(f"Could not reach Google: {exc.reason}")
                raise err from exc

        if last_error and attempts > 1 and "content" not in locals():
            raise last_error

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError("Invalid JSON response from Google") from exc

        return self._extract_message(payload)

    @staticmethod
    def _extract_message(payload: dict) -> str:
        """Extract the text message from Google's response."""
        try:
            candidates = payload.get("candidates", [])
            if not candidates:
                # Check for blocking/safety reasons
                if "promptFeedback" in payload:
                    feedback = payload["promptFeedback"]
                    if "blockReason" in feedback:
                        return f"[BLOCKED: {feedback['blockReason']}]"
                raise ProviderError("Google response contained no candidates")

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            if not parts:
                raise ProviderError("Google response did not include content parts")

            # Concatenate all text parts
            text_parts = []
            for part in parts:
                if "text" in part:
                    text_parts.append(part["text"])

            if not text_parts:
                raise ProviderError("Google response did not include text content")

            return "".join(text_parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected Google response structure") from exc

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
                # Default to gemini-1.5-flash pricing if unknown
                model_key = "gemini-1.5-flash"

        pricing = PRICING[model_key]

        # Rough token estimation: ~4 chars per token
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        # Cost per million tokens
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


__all__ = ["GoogleProvider", "API_KEY_ENV", "PRICING"]
