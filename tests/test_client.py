import io
import socket
import urllib.error

import pytest

from llm_tester.client import OllamaClient, OllamaError


def test_extract_message_supports_new_shape() -> None:
    payload = {"message": {"content": "hello"}}
    assert OllamaClient.extract_message(payload) == "hello"


def test_extract_message_supports_legacy_shape() -> None:
    payload = {"response": "legacy text"}
    assert OllamaClient.extract_message(payload) == "legacy text"


def test_extract_message_raises_on_missing() -> None:
    with pytest.raises(OllamaError):
        OllamaClient.extract_message({"not": "present"})


def test_from_env_applies_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_URL", "http://example.com")
    client = OllamaClient.from_env(timeout=45, retries=2)

    assert client.base_url == "http://example.com"
    assert client.timeout == 45
    assert client.retries == 2


def test_generate_converts_socket_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(base_url="http://example.com")

    def _fake_urlopen(*args, **kwargs):  # noqa: ANN001
        raise socket.timeout

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    with pytest.raises(OllamaError) as excinfo:
        client.generate("hello", "model")

    assert "timed out" in str(excinfo.value)


def test_generate_retries_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(base_url="http://example.com", retries=1)

    class _FakeResponse:
        def __init__(self, payload: str) -> None:
            self.payload = payload
            self.status = 200

        def read(self) -> bytes:
            return self.payload.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    calls = []

    def _fake_urlopen(*args, **kwargs):  # noqa: ANN001
        calls.append(True)
        if len(calls) == 1:
            raise socket.timeout
        return _FakeResponse('{"response": "ok"}')

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    assert client.generate("hello", "model") == "ok"
    assert len(calls) == 2


def test_generate_retries_http_500(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(base_url="http://example.com", retries=2)

    class _FakeResponse:
        def __init__(self, payload: str) -> None:
            self.payload = payload
            self.status = 200

        def read(self) -> bytes:
            return self.payload.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    def _http_error(code: int) -> urllib.error.HTTPError:
        return urllib.error.HTTPError(
            url="http://example.com", code=code, msg="error", hdrs={}, fp=io.BytesIO(b"fail")
        )

    responses = [_http_error(500), _http_error(502), _FakeResponse('{"response": "ok"}')]

    def _fake_urlopen(*args, **kwargs):  # noqa: ANN001
        response = responses.pop(0)
        if isinstance(response, urllib.error.HTTPError):
            raise response
        return response

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    assert client.generate("hello", "model") == "ok"
