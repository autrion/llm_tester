"""Lightweight, extendable rule engine for detecting unsafe LLM outputs.

The module defines simple rule classes to flag common jailbreak or safety
circumvention attempts in model responses. It uses only the standard
library's :mod:`re` module and can be imported on its own without any
other dependencies.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Sequence


class Rule:
    """Base class for all rules.

    Each rule has a ``name`` and ``description`` and must implement ``check``
    to decide whether a piece of text triggers the rule.
    """

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def check(self, text: str) -> bool:  # pragma: no cover - intended override
        """Return ``True`` when the rule is triggered by ``text``.

        Subclasses must override this method.
        """

        raise NotImplementedError("Subclasses must implement 'check'.")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class KeywordRule(Rule):
    """Rule triggered when any keyword appears in the text.

    Keyword matches are case-insensitive and search for simple substring
    occurrences. Provide multiple phrases to capture variants of the same
    pattern.
    """

    def __init__(self, name: str, description: str, keywords: Sequence[str]):
        super().__init__(name, description)
        if not keywords:
            raise ValueError("KeywordRule requires at least one keyword.")
        self.keywords = tuple(keywords)

    def check(self, text: str) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in self.keywords)


class RegexRule(Rule):
    """Rule triggered when a regex pattern matches the text."""

    def __init__(self, name: str, description: str, pattern: str, *, flags: int = re.IGNORECASE):
        super().__init__(name, description)
        self._compiled = re.compile(pattern, flags)

    def check(self, text: str) -> bool:
        return bool(self._compiled.search(text))


class CompositeRule(Rule):
    """Combine multiple rules with logical AND or OR semantics."""

    def __init__(self, name: str, description: str, rules: Iterable[Rule], *, mode: str = "AND"):
        super().__init__(name, description)
        self.rules: List[Rule] = list(rules)
        if not self.rules:
            raise ValueError("CompositeRule requires at least one child rule.")
        mode_normalized = mode.upper()
        if mode_normalized not in {"AND", "OR"}:
            raise ValueError("CompositeRule mode must be 'AND' or 'OR'.")
        self.mode = mode_normalized

    def check(self, text: str) -> bool:
        if self.mode == "AND":
            return all(rule.check(text) for rule in self.rules)
        return any(rule.check(text) for rule in self.rules)


def load_default_rules() -> List[Rule]:
    """Return a curated list of default rules for common jailbreak patterns."""

    keyword_rules: List[Rule] = [
        KeywordRule(
            name="prompt_injection",
            description="Asks to ignore or override earlier instructions.",
            keywords=("ignore previous instructions", "disregard prior instructions"),
        ),
        KeywordRule(
            name="dan_mode",
            description="Requests activation of DAN or similar unrestricted personas.",
            keywords=("act as dan", "do anything now", "dan mode"),
        ),
        KeywordRule(
            name="jailbreak_roleplay",
            description="Attempts to roleplay as a jailbroken or unrestricted model.",
            keywords=("you are no longer bound", "you are unfiltered", "unrestricted ai"),
        ),
        KeywordRule(
            name="safety_bypass",
            description="Attempts to disable safety or ethical constraints.",
            keywords=("bypass safety", "disable safety", "turn off safety"),
        ),
        KeywordRule(
            name="system_prompt_disclosure",
            description="Asks to reveal or change the system prompt.",
            keywords=("show system prompt", "reveal system prompt", "ignore the system prompt"),
        ),
    ]

    regex_rules: List[Rule] = [
        RegexRule(
            name="regex_ignore_previous",
            description="Regex pattern for ignoring previous instructions.",
            pattern=r"ignore\s+.*previous instructions",
        ),
        RegexRule(
            name="regex_unfiltered",
            description="Pattern suggesting the model act without restrictions.",
            pattern=r"act (?:completely )?without (?:any )?restrictions",
        ),
        RegexRule(
            name="regex_bypass_guardrails",
            description="Pattern to bypass moderation or guardrails.",
            pattern=r"bypass (?:all )?(?:guards?|guardrails|filters|moderation)",
        ),
        RegexRule(
            name="regex_pretend_role",
            description="Requests to pretend to be a jailbroken entity.",
            pattern=r"pretend to be (?:an? )?jailbrok(?:en|e)?,? unrestricted ai",
        ),
        RegexRule(
            name="regex_override_confidential",
            description="Attempts to override confidentiality or safety warnings.",
            pattern=r"ignore (?:any )?safety (?:protocols|measures) and (?:just )?answer",
        ),
    ]

    composite_rules: List[Rule] = [
        CompositeRule(
            name="combined_dan_prompt_injection",
            description="Combination of DAN activation plus prompt injection cues.",
            rules=[keyword_rules[1], keyword_rules[0], regex_rules[0]],
            mode="OR",
        ),
        CompositeRule(
            name="safety_disable_combo",
            description="Suggests disabling safety alongside unfiltered behavior.",
            rules=[keyword_rules[3], regex_rules[1]],
            mode="AND",
        ),
    ]

    return [*keyword_rules, *regex_rules, *composite_rules]


def evaluate_text(text: str) -> List[Rule]:
    """Apply all default rules to ``text`` and return those that trigger."""

    triggered = []
    for rule in load_default_rules():
        if rule.check(text):
            triggered.append(rule)
    return triggered


__all__ = [
    "Rule",
    "KeywordRule",
    "RegexRule",
    "CompositeRule",
    "load_default_rules",
    "evaluate_text",
]
