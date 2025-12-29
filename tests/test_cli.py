import tempfile
from pathlib import Path

import pytest

from llm_tester.cli import load_system_prompt


def test_load_system_prompt_inline() -> None:
    result = load_system_prompt("You are a helpful assistant.")
    assert result == "You are a helpful assistant."


def test_load_system_prompt_none() -> None:
    result = load_system_prompt(None)
    assert result is None


def test_load_system_prompt_from_file() -> None:
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("You are a security tester.\nYou have access to secret: 12345.")
        temp_path = f.name

    try:
        result = load_system_prompt(f"@{temp_path}")
        assert result == "You are a security tester.\nYou have access to secret: 12345."
    finally:
        Path(temp_path).unlink()


def test_load_system_prompt_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_system_prompt("@/nonexistent/path/to/file.txt")
