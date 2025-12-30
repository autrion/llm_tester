import json
import tempfile
from pathlib import Path

import pytest

from llm_tester.rule_loader import load_rules_from_json
from llm_tester.rules import KeywordRule, RegexRule


def test_load_keyword_rules_from_json() -> None:
    rules_data = {
        "keyword_rules": [
            {
                "name": "test_rule",
                "description": "A test rule",
                "keywords": ["test", "example"],
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(rules_data, f)
        temp_path = f.name

    try:
        rules = load_rules_from_json(temp_path)
        assert len(rules) == 1
        assert isinstance(rules[0], KeywordRule)
        assert rules[0].name == "test_rule"
        assert "test" in rules[0].keywords
    finally:
        Path(temp_path).unlink()


def test_load_regex_rules_from_json() -> None:
    rules_data = {
        "regex_rules": [
            {
                "name": "pattern_rule",
                "description": "A pattern rule",
                "pattern": r"\btest\b",
                "flags": 2,
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(rules_data, f)
        temp_path = f.name

    try:
        rules = load_rules_from_json(temp_path)
        assert len(rules) == 1
        assert isinstance(rules[0], RegexRule)
        assert rules[0].name == "pattern_rule"
    finally:
        Path(temp_path).unlink()


def test_load_mixed_rules_from_json() -> None:
    rules_data = {
        "keyword_rules": [
            {
                "name": "keyword_test",
                "description": "Keyword",
                "keywords": ["foo"],
            }
        ],
        "regex_rules": [
            {
                "name": "regex_test",
                "description": "Regex",
                "pattern": r"bar",
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(rules_data, f)
        temp_path = f.name

    try:
        rules = load_rules_from_json(temp_path)
        assert len(rules) == 2
    finally:
        Path(temp_path).unlink()


def test_load_rules_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_rules_from_json("/nonexistent/path.json")


def test_load_rules_invalid_json() -> None:
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write("invalid json content")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_rules_from_json(temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_rules_empty_file() -> None:
    rules_data = {}

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(rules_data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="No rules found"):
            load_rules_from_json(temp_path)
    finally:
        Path(temp_path).unlink()
