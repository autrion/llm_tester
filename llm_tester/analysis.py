"""Response analysis helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from llm_tester.rules import Rule, evaluate_with_default_rules


@dataclass(frozen=True)
class ResponseAnalysis:
    """Structured result of analyzing a model response."""

    response_length: int
    triggered_rules: List[str]


def analyze_response(response: str, rules: Sequence[Rule] | None = None) -> ResponseAnalysis:
    """Analyze a response and return triggered rule names and metadata."""

    if rules is None:
        triggered = evaluate_with_default_rules(response)
    else:
        triggered = [rule for rule in rules if rule.check(response)]

    return ResponseAnalysis(
        response_length=len(response),
        triggered_rules=[rule.name for rule in triggered],
    )


__all__ = ["ResponseAnalysis", "analyze_response"]
