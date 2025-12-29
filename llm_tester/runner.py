"""Core orchestration for running prompts against Ollama or demo mode."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

from llm_tester.analysis import analyze_response
from llm_tester.client import OllamaClient, OllamaError
from llm_tester.prompts import Prompt
from llm_tester.rules import Rule

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # type: ignore

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
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
) -> ResultRecord:
    if demo_mode:
        response = f"[DEMO RESPONSE] Model {model} would respond to: {prompt.text}"
    else:
        if client is None:
            raise OllamaError("LLM client is not configured")
        response = client.generate(prompt.text, model, system=system_prompt)

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
    )


def run_assessment(
    prompts: Sequence[Prompt],
    model: str,
    *,
    client: OllamaClient | None = None,
    demo_mode: bool | None = None,
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
    workers: int = 1,
    show_progress: bool = True,
) -> List[ResultRecord]:
    """Run assessment against multiple prompts.

    Args:
        prompts: List of prompts to test
        model: Model identifier
        client: Ollama client instance
        demo_mode: Whether to run in demo mode
        analyze_prompt: Whether to analyze prompts themselves
        rules: Rules for response analysis
        prompt_rules: Rules for prompt analysis
        system_prompt: Optional system prompt
        workers: Number of parallel workers (1 = sequential)
        show_progress: Whether to show progress bar

    Returns:
        List of result records
    """
    results: List[ResultRecord] = []
    effective_demo = bool(os.environ.get(DEMO_ENV)) if demo_mode is None else demo_mode

    # Determine if we can show progress
    use_progress = show_progress and tqdm is not None

    if workers > 1:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_prompt = {
                executor.submit(
                    run_prompt,
                    prompt,
                    model,
                    client=client,
                    demo_mode=effective_demo,
                    analyze_prompt=analyze_prompt,
                    rules=rules,
                    prompt_rules=prompt_rules,
                    system_prompt=system_prompt,
                ): prompt
                for prompt in prompts
            }

            # Use tqdm if available
            futures = (
                tqdm(as_completed(future_to_prompt), total=len(prompts), desc="Processing prompts")
                if use_progress
                else as_completed(future_to_prompt)
            )

            for future in futures:
                try:
                    record = future.result()
                    results.append(record)
                except Exception as exc:  # pragma: no cover
                    # In parallel mode, we collect errors but continue
                    prompt = future_to_prompt[future]
                    raise OllamaError(f"Failed to process prompt: {prompt.text[:50]}...") from exc
    else:
        # Sequential processing
        prompt_iter = tqdm(prompts, desc="Processing prompts") if use_progress else prompts

        for prompt in prompt_iter:
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
