"""Lightweight AnythingLLM client used by the CLI runner."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


DEFAULT_BASE_URL = "http://localhost:3001"
DEFAULT_WORKSPACE = "default"
API_KEY_ENV = "ANYTHINGLLM_API_KEY"
BASE_URL_ENV = "ANYTHINGLLM_URL"
WORKSPACE_ENV = "ANYTHINGLLM_WORKSPACE"


class AnythingLLMError(RuntimeError):
    """Raised when the AnythingLLM API returns an error."""


@dataclass
class AnythingLLMClient:
    """Simple HTTP client for AnythingLLM's workspace chat endpoint."""

    base_url: str
    api_key: str
    workspace: str = DEFAULT_WORKSPACE
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "AnythingLLMClient":
        """Create a client using environment configuration.

        Required:
        - ANYTHINGLLM_API_KEY

        Optional (with defaults):
        - ANYTHINGLLM_URL (defaults to http://localhost:3001)
        - ANYTHINGLLM_WORKSPACE (defaults to "default")
        """

        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise AnythingLLMError(
                "Missing API key. Set the ANYTHINGLLM_API_KEY environment variable."
            )

        base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
        workspace = os.environ.get(WORKSPACE_ENV, DEFAULT_WORKSPACE)
        return cls(base_url=base_url, api_key=api_key, workspace=workspace)

    def _build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1/workspaces/{self.workspace}/chat"

    def generate(self, prompt: str, model: str) -> str:
        """Send a prompt to AnythingLLM and return the response text."""

        payload = {
            "message": prompt,
            "mode": "chat",
            "model": model,
            "attachments": [],
            "threadId": None,
        }
        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self._build_url(),
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                content = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - thin wrapper
            body = exc.read().decode("utf-8")
            raise AnythingLLMError(
                f"AnythingLLM request failed with status {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:  # pragma: no cover - thin wrapper
            raise AnythingLLMError(f"Could not reach AnythingLLM: {exc.reason}") from exc

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AnythingLLMError("Invalid JSON response from AnythingLLM") from exc

        return self._extract_message(payload)

    @staticmethod
    def _extract_message(payload: dict) -> str:
        """Extract the text message from AnythingLLM's response shape."""

        # Newer AnythingLLM releases return the message content nested under
        # a "message" object, but older ones may return "response". We attempt
        # both to keep the client resilient to small API differences.
        message_block = payload.get("message")
        if isinstance(message_block, dict):
            content = message_block.get("content") or message_block.get("message")
            if content:
                return str(content)

        if "response" in payload:
            return str(payload["response"])

        raise AnythingLLMError("AnythingLLM response did not include message content")
