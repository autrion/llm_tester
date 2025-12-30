"""Load custom rules from JSON files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from llm_tester.rules import KeywordRule, RegexRule, Rule


def load_rules_from_json(file_path: str | Path) -> List[Rule]:
    """Load custom rules from a JSON file.

    Expected JSON format:
    {
        "keyword_rules": [
            {
                "name": "rule_name",
                "description": "Rule description",
                "keywords": ["keyword1", "keyword2"]
            }
        ],
        "regex_rules": [
            {
                "name": "rule_name",
                "description": "Rule description",
                "pattern": "regex_pattern",
                "flags": 2  # Optional: re.IGNORECASE = 2
            }
        ]
    }

    Args:
        file_path: Path to JSON file containing rule definitions

    Returns:
        List of Rule objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid or malformed
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {file_path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in rules file: {exc}") from exc

    rules: List[Rule] = []

    # Load keyword rules
    for rule_data in data.get("keyword_rules", []):
        try:
            rule = KeywordRule(
                name=rule_data["name"],
                description=rule_data["description"],
                keywords=rule_data["keywords"],
            )
            rules.append(rule)
        except KeyError as exc:
            raise ValueError(f"Missing required field in keyword rule: {exc}") from exc

    # Load regex rules
    for rule_data in data.get("regex_rules", []):
        try:
            rule = RegexRule(
                name=rule_data["name"],
                description=rule_data["description"],
                pattern=rule_data["pattern"],
                flags=rule_data.get("flags", 2),  # Default to IGNORECASE
            )
            rules.append(rule)
        except KeyError as exc:
            raise ValueError(f"Missing required field in regex rule: {exc}") from exc

    if not rules:
        raise ValueError("No rules found in JSON file")

    return rules


__all__ = ["load_rules_from_json"]
