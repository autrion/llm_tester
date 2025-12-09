"""AnythingLLM client abstraction."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE_URL = "http://localhost:3001"
DEFAULT_WORKSPACE = "default"
API_KEY_ENV = "ANYTHINGLLM_API_KEY"
BASE_URL_ENV = "ANYTHINGLLM_URL"
WORKSPACE_ENV = "ANYTHINGLLM_WORKSPACE"


class AnythingLLMError(RuntimeError):
    """Raised when AnythingLLM returns an error or unexpected payload."""


@dataclass
class AnythingLLMClient:
    """Minimal HTTP client for AnythingLLM's workspace chat endpoint."""

    base_url: str
    api_key: str
    workspace: str = DEFAULT_WORKSPACE
    timeout: int = 30
    debug: bool = False

    @classmethod
    def from_env(cls, *, debug: bool = False) -> "AnythingLLMClient":
        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise AnythingLLMError("Missing API key. Set ANYTHINGLLM_API_KEY.")

        base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
        workspace = os.environ.get(WORKSPACE_ENV, DEFAULT_WORKSPACE)
        return cls(base_url=base_url, api_key=api_key, workspace=workspace, debug=debug)

    def _build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1/workspaces/{self.workspace}/chat"

    def generate(self, prompt: str, model: str) -> str:
        payload = {
            "message": prompt,
            "mode": "chat",
            "model": model,
            "attachments": [],
            "threadId": None,
        }
        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._build_url(),
            data=encoded,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                if self.debug:
                    print(f"AnythingLLM status: {getattr(response, 'status', 'unknown')}", file=sys.stderr)
                content = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
            message = exc.read().decode("utf-8")
            raise AnythingLLMError(f"AnythingLLM returned HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network dependent
            raise AnythingLLMError(f"Could not reach AnythingLLM: {exc.reason}") from exc

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AnythingLLMError("Invalid JSON response from AnythingLLM") from exc

        return self.extract_message(payload)

    @staticmethod
    def extract_message(payload: dict) -> str:
        """Extract the text message from AnythingLLM's response shape."""

        message = payload.get("message")
        if isinstance(message, dict):
            content = message.get("content") or message.get("message")
            if content:
                return str(content)

        legacy_response = payload.get("response")
        if legacy_response is not None:
            return str(legacy_response)

        raise AnythingLLMError("AnythingLLM response did not include message content")


__all__ = [
    "API_KEY_ENV",
    "BASE_URL_ENV",
    "WORKSPACE_ENV",
    "AnythingLLMClient",
    "AnythingLLMError",
]
