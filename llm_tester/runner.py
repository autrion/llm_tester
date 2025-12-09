"""Core orchestration for running prompts against Ollama or demo mode."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

from llm_tester.analysis import analyze_response
from llm_tester.client import OllamaClient, OllamaError
from llm_tester.prompts import Prompt

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


def run_prompt(
    prompt: Prompt,
    model: str,
    *,
    client: OllamaClient | None,
    demo_mode: bool,
) -> ResultRecord:
    if demo_mode:
        response = f"[DEMO RESPONSE] Model {model} would respond to: {prompt.text}"
    else:
        if client is None:
            raise OllamaError("LLM client is not configured")
        response = client.generate(prompt.text, model)

    analysis = analyze_response(response)
    return ResultRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        prompt=prompt.text,
        prompt_category=prompt.category,
        response=response,
        model=model,
        response_length=analysis.response_length,
        triggered_rules=analysis.triggered_rules,
    )


def run_assessment(
    prompts: Sequence[Prompt],
    model: str,
    *,
    client: OllamaClient | None = None,
    demo_mode: bool | None = None,
) -> List[ResultRecord]:
    results: List[ResultRecord] = []
    effective_demo = bool(os.environ.get(DEMO_ENV)) if demo_mode is None else demo_mode

    for prompt in prompts:
        record = run_prompt(prompt, model, client=client, demo_mode=effective_demo)
        results.append(record)
    return results


def serialize_results(records: Iterable[ResultRecord]) -> List[dict]:
    return [asdict(record) for record in records]


__all__ = ["ResultRecord", "run_assessment", "run_prompt", "serialize_results", "DEMO_ENV"]
