import socket

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


def test_generate_converts_socket_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(base_url="http://example.com")

    def _fake_urlopen(*args, **kwargs):  # noqa: ANN001
        raise socket.timeout

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    with pytest.raises(OllamaError) as excinfo:
        client.generate("hello", "model")

    assert "timed out" in str(excinfo.value)
