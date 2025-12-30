"""Async parallel execution engine for high-performance LLM testing."""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Sequence

from llm_tester.analysis import analyze_response
from llm_tester.prompts import Prompt
from llm_tester.providers import LLMProvider, ProviderError
from llm_tester.rules import Rule
from llm_tester.runner import DEMO_ENV, ResultRecord


@dataclass
class AsyncProgressCallback:
    """Callback for progress updates during async execution."""

    total: int
    completed: int = 0

    def update(self, increment: int = 1) -> None:
        """Update progress counter."""
        self.completed += increment

    def get_progress(self) -> tuple[int, int]:
        """Return (completed, total) tuple."""
        return self.completed, self.total

    def get_percentage(self) -> float:
        """Return completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100


async def run_prompt_async(
    prompt: Prompt,
    model: str,
    *,
    provider: LLMProvider | None,
    demo_mode: bool,
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
    semaphore: asyncio.Semaphore | None = None,
    progress: AsyncProgressCallback | None = None,
) -> ResultRecord:
    """Run a single prompt asynchronously.

    Args:
        prompt: Prompt to test
        model: Model identifier
        provider: LLM provider instance
        demo_mode: Use demo mode
        analyze_prompt: Whether to analyze the prompt itself
        rules: Rules to evaluate against response
        prompt_rules: Rules to evaluate against prompt
        system_prompt: Optional system prompt
        semaphore: Semaphore for concurrency control
        progress: Progress callback for updates

    Returns:
        ResultRecord with test results
    """
    # Acquire semaphore if provided (limits concurrency)
    if semaphore:
        async with semaphore:
            result = await _run_single_prompt(
                prompt,
                model,
                provider=provider,
                demo_mode=demo_mode,
                analyze_prompt=analyze_prompt,
                rules=rules,
                prompt_rules=prompt_rules,
                system_prompt=system_prompt,
            )
    else:
        result = await _run_single_prompt(
            prompt,
            model,
            provider=provider,
            demo_mode=demo_mode,
            analyze_prompt=analyze_prompt,
            rules=rules,
            prompt_rules=prompt_rules,
            system_prompt=system_prompt,
        )

    # Update progress if callback provided
    if progress:
        progress.update()

    return result


async def _run_single_prompt(
    prompt: Prompt,
    model: str,
    *,
    provider: LLMProvider | None,
    demo_mode: bool,
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
) -> ResultRecord:
    """Internal function to run a single prompt (without semaphore)."""
    cost = 0.0
    provider_name = None

    if demo_mode:
        # Simulate async delay for demo mode
        await asyncio.sleep(0.1)
        response = f"[DEMO RESPONSE] Model {model} would respond to: {prompt.text}"
        provider_name = "demo"
    else:
        if provider is None:
            raise ProviderError("LLM provider is not configured")

        # Run synchronous provider call in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, provider.generate, prompt.text, model, system_prompt
        )

        provider_name = provider.get_provider_name()
        cost = provider.estimate_cost(prompt.text, response, model)

    # Run analysis (also in executor if needed)
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


async def run_assessment_async(
    prompts: Sequence[Prompt],
    model: str,
    *,
    provider: LLMProvider | None = None,
    demo_mode: bool | None = None,
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
    concurrency: int = 10,
    progress_callback: AsyncProgressCallback | None = None,
) -> List[ResultRecord]:
    """Run assessment asynchronously with controlled concurrency.

    Args:
        prompts: List of prompts to test
        model: Model identifier
        provider: LLM provider instance
        demo_mode: Use demo mode
        analyze_prompt: Whether to analyze prompts
        rules: Rules for response evaluation
        prompt_rules: Rules for prompt evaluation
        system_prompt: Optional system prompt
        concurrency: Maximum concurrent requests (default: 10)
        progress_callback: Optional callback for progress updates

    Returns:
        List of ResultRecords
    """
    effective_demo = bool(os.environ.get(DEMO_ENV)) if demo_mode is None else demo_mode

    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrency)

    # Create progress callback if not provided
    if progress_callback is None:
        progress_callback = AsyncProgressCallback(total=len(prompts))

    # Create tasks for all prompts
    tasks = [
        run_prompt_async(
            prompt,
            model,
            provider=provider,
            demo_mode=effective_demo,
            analyze_prompt=analyze_prompt,
            rules=rules,
            prompt_rules=prompt_rules,
            system_prompt=system_prompt,
            semaphore=semaphore,
            progress=progress_callback,
        )
        for prompt in prompts
    ]

    # Execute all tasks concurrently and gather results
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and collect successful results
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Log error but continue with other results
            print(f"Error processing prompt {i + 1}: {result}")
        else:
            successful_results.append(result)

    return successful_results


def run_assessment_sync_wrapper(
    prompts: Sequence[Prompt],
    model: str,
    *,
    provider: LLMProvider | None = None,
    demo_mode: bool | None = None,
    analyze_prompt: bool = False,
    rules: Sequence[Rule] | None = None,
    prompt_rules: Sequence[Rule] | None = None,
    system_prompt: str | None = None,
    concurrency: int = 10,
) -> List[ResultRecord]:
    """Synchronous wrapper for async assessment (for CLI compatibility).

    This allows the async engine to be used from synchronous code.
    """
    return asyncio.run(
        run_assessment_async(
            prompts,
            model,
            provider=provider,
            demo_mode=demo_mode,
            analyze_prompt=analyze_prompt,
            rules=rules,
            prompt_rules=prompt_rules,
            system_prompt=system_prompt,
            concurrency=concurrency,
        )
    )


__all__ = [
    "run_prompt_async",
    "run_assessment_async",
    "run_assessment_sync_wrapper",
    "AsyncProgressCallback",
]
