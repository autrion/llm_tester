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


def _evaluate_rules(text: str, rules: Sequence[Rule] | None) -> List[Rule]:
    if rules is None:
        return evaluate_with_default_rules(text)
    return [rule for rule in rules if rule.check(text)]


def analyze_response(
    response: str,
    rules: Sequence[Rule] | None = None,
    *,
    include_prompt_analysis: bool = False,
    prompt: str | None = None,
    prompt_rules: Sequence[Rule] | None = None,
) -> ResponseAnalysis:
    """Analyze a response and return triggered rule names and metadata.

    ``include_prompt_analysis`` keeps backward compatibility by defaulting to
    ``False``. When set to ``True`` and a ``prompt`` is provided, the prompt text
    is evaluated with either ``prompt_rules`` (if provided) or the main
    ``rules``.
    """

    triggered_rule_names: List[str] = []
    seen_names = set()

    for rule in _evaluate_rules(response, rules):
        triggered_rule_names.append(rule.name)
        seen_names.add(rule.name)

    if include_prompt_analysis and prompt is not None:
        for rule in _evaluate_rules(prompt, prompt_rules or rules):
            if rule.name in seen_names:
                continue
            triggered_rule_names.append(rule.name)
            seen_names.add(rule.name)

    return ResponseAnalysis(
        response_length=len(response),
        triggered_rules=triggered_rule_names,
    )


__all__ = ["ResponseAnalysis", "analyze_response"]
