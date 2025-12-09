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
