"""Ollama client abstraction."""
from __future__ import annotations

import json
import os
import socket
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
    retries: int = 0

    @classmethod
    def from_env(
        cls, *, timeout: int = 30, debug: bool = False, retries: int = 0
    ) -> "OllamaClient":
        base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
        return cls(base_url=base_url, timeout=timeout, debug=debug, retries=retries)

    def _build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/generate"

    def generate(self, prompt: str, model: str, system: str | None = None) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system is not None:
            payload["system"] = system
        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._build_url(),
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
                            f"Ollama status: {getattr(response, 'status', 'unknown')}",
                            file=sys.stderr,
                        )
                    content = response.read().decode("utf-8")
                break
            except socket.timeout as exc:  # pragma: no cover - network dependent
                last_error = OllamaError(
                    "Ollama request timed out. Increase the timeout or check model performance."
                )
                if attempt < attempts - 1:
                    if self.debug:
                        print(
                            f"Request timed out (attempt {attempt + 1}/{attempts}), retrying...",
                            file=sys.stderr,
                        )
                    continue
                raise last_error from exc
            except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
                message = exc.read().decode("utf-8")
                err = OllamaError(f"Ollama returned HTTP {exc.code}: {message}")
                if attempt < attempts - 1 and exc.code >= 500:
                    last_error = err
                    if self.debug:
                        print(
                            f"HTTP {exc.code} from Ollama (attempt {attempt + 1}/{attempts}), retrying...",
                            file=sys.stderr,
                        )
                    continue
                raise err from exc
            except urllib.error.URLError as exc:  # pragma: no cover - network dependent
                err = OllamaError(f"Could not reach Ollama: {exc.reason}")
                raise err from exc

        if last_error and attempts > 1 and "content" not in locals():
            raise last_error

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
