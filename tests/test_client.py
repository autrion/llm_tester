import pytest

from llm_tester.client import AnythingLLMClient, AnythingLLMError


def test_extract_message_supports_new_shape() -> None:
    payload = {"message": {"content": "hello"}}
    assert AnythingLLMClient.extract_message(payload) == "hello"


def test_extract_message_supports_legacy_shape() -> None:
    payload = {"response": "legacy text"}
    assert AnythingLLMClient.extract_message(payload) == "legacy text"


def test_extract_message_raises_on_missing() -> None:
    with pytest.raises(AnythingLLMError):
        AnythingLLMClient.extract_message({"not": "present"})
