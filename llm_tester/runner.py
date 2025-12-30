"""Core orchestration for running prompts against LLM providers or demo mode."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

from llm_tester.analysis import analyze_response
from llm_tester.client import OllamaClient, OllamaError
from llm_tester.prompts import Prompt
from llm_tester.providers import LLMProvider, ProviderError
from llm_tester.rules import Rule

DEMO_ENV = "LLM_TESTER_DEMO"


@dataclass
class ResultRecord:
    timestamp: str
    prompt: str
    prompt_category: str | None
    response: str
    model: str
    response_length: int
    triggered_rules: List[str]
    cost_usd: float = 0.0
    provider: str | None = None


def run_prompt(
    prompt: Prompt,
    model: str,
    *,
    client: OllamaClient | LLMProvider | None,
    demo_mode: bool,
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
) -> ResultRecord:
    cost = 0.0
    provider_name = None

    if demo_mode:
        response = f"[DEMO RESPONSE] Model {model} would respond to: {prompt.text}"
        provider_name = "demo"
    else:
        if client is None:
            raise ProviderError("LLM client is not configured")

        # Support both old OllamaClient and new LLMProvider
        try:
            response = client.generate(prompt.text, model, system=system_prompt)

            # Get provider name and cost if using new provider system
            if isinstance(client, LLMProvider):
                provider_name = client.get_provider_name()
                cost = client.estimate_cost(prompt.text, response, model)
            else:
                # Legacy OllamaClient
                provider_name = "ollama"
                cost = 0.0

        except (OllamaError, ProviderError) as exc:
            # Re-raise as ProviderError for consistency
            if isinstance(exc, OllamaError):
                raise ProviderError(str(exc)) from exc
            raise

    analysis = analyze_response(
        response,
        rules=rules,
        include_prompt_analysis=analyze_prompt,
        prompt=prompt.text,
        prompt_rules=prompt_rules,
    )
    return ResultRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        prompt=prompt.text,
        prompt_category=prompt.category,
        response=response,
        model=model,
        response_length=analysis.response_length,
        triggered_rules=analysis.triggered_rules,
        cost_usd=cost,
        provider=provider_name,
    )


def run_assessment(
    prompts: Sequence[Prompt],
    model: str,
    *,
    client: OllamaClient | LLMProvider | None = None,
    demo_mode: bool | None = None,
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
) -> List[ResultRecord]:
    results: List[ResultRecord] = []
    effective_demo = bool(os.environ.get(DEMO_ENV)) if demo_mode is None else demo_mode

    for prompt in prompts:
        record = run_prompt(
            prompt,
            model,
            client=client,
            demo_mode=effective_demo,
            analyze_prompt=analyze_prompt,
            rules=rules,
            prompt_rules=prompt_rules,
            system_prompt=system_prompt,
        )
        results.append(record)
    return results


def serialize_results(records: Iterable[ResultRecord]) -> List[dict]:
    return [asdict(record) for record in records]


__all__ = ["ResultRecord", "run_assessment", "run_prompt", "serialize_results", "DEMO_ENV"]
