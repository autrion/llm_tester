"""Ollama client abstraction."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE_URL = "http://localhost:11434"
BASE_URL_ENV = "OLLAMA_URL"


class OllamaError(RuntimeError):
    """Raised when Ollama returns an error or unexpected payload."""


@dataclass
class OllamaClient:
    """Minimal HTTP client for the Ollama generate endpoint."""

    base_url: str
    timeout: int = 30
    debug: bool = False

    @classmethod
    def from_env(cls, *, debug: bool = False) -> "OllamaClient":
        base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
        return cls(base_url=base_url, debug=debug)

    def _build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/generate"

    def generate(self, prompt: str, model: str) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._build_url(),
            data=encoded,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                if self.debug:
                    print(f"Ollama status: {getattr(response, 'status', 'unknown')}", file=sys.stderr)
                content = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
            message = exc.read().decode("utf-8")
            raise OllamaError(f"Ollama returned HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network dependent
            raise OllamaError(f"Could not reach Ollama: {exc.reason}") from exc

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaError("Invalid JSON response from Ollama") from exc

        return self.extract_message(payload)

    @staticmethod
    def extract_message(payload: dict) -> str:
        """Extract the text message from Ollama's response shape."""

        message = payload.get("message")
        if isinstance(message, dict):
            content = message.get("content") or message.get("message")
            if content:
                return str(content)

        response_text = payload.get("response")
        if response_text is not None:
            return str(response_text)

        raise OllamaError("Ollama response did not include message content")


__all__ = [
    "BASE_URL_ENV",
    "OllamaClient",
    "OllamaError",
]
