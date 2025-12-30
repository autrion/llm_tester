"""Command-line interface for the LLM Tester toolkit."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Iterable, List

from llm_tester import prompts as prompt_loader
from llm_tester.async_runner import run_assessment_sync_wrapper
from llm_tester.client import BASE_URL_ENV, OllamaClient, OllamaError
from llm_tester.logging_config import setup_logging
from llm_tester.reporting import generate_html_report
from llm_tester.rule_loader import load_rules_from_json
from llm_tester.runner import DEMO_ENV, ResultRecord, run_assessment, serialize_results


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run security prompts against an LLM endpoint.")
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "google", "azure", "ollama"],
        default="ollama",
        help="LLM provider to use (default: ollama).",
    )
    parser.add_argument("--model", default="gpt-4o-mini", help="Target model identifier.")
    parser.add_argument("--prompts-file", default="prompts.txt", help="Path to the prompt list file.")
    parser.add_argument("--max-prompts", type=int, default=None, help="Maximum number of prompts to process.")
    parser.add_argument("--output", default="results.csv", help="Output file path (.csv or .jsonl).")
    parser.add_argument("--ollama-url", default=None, help="Ollama base URL (overrides env). Only for --provider=ollama.")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds.")
    parser.add_argument(
        "--retries",
        type=int,
        default=0,
        help="Number of retries for transient errors (timeouts, HTTP 5xx).",
    )
    parser.add_argument("--demo", action="store_true", help="Run in offline demo mode without network calls.")
    parser.add_argument("--format", choices=["csv", "jsonl", "html", "sarif"], default=None, help="Output format (csv, jsonl, html, sarif).")
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="System prompt to inject (inline text or @file path).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for processing prompts (default: 1).",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar display.",
    )
    parser.add_argument(
        "--rules-file",
        default=None,
        help="Path to custom rules JSON file.",
    )
    parser.add_argument(
        "--html-report",
        default=None,
        help="Generate HTML report at specified path.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO).",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Path to log file (enables file logging).",
    )
    return parser.parse_args(argv)


def _write_csv(output_path: Path, records: Iterable[dict]) -> None:
    rows = list(records)
    if not rows:
        return
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_jsonl(output_path: Path, records: Iterable[dict]) -> None:
    with output_path.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_output(
    path: Path,
    records: Iterable[dict] | List[ResultRecord],
    forced_format: str | None = None,
) -> None:
    """Save output in various formats."""
    suffix = forced_format or path.suffix.lstrip(".").lower()

    # Convert ResultRecord objects to dicts if needed
    if records and isinstance(list(records)[0], ResultRecord):
        result_objects = list(records)
        dict_records = serialize_results(result_objects)
    else:
        dict_records = list(records)
        result_objects = None

    if suffix == "csv":
        _write_csv(path, dict_records)
    elif suffix == "jsonl":
        _write_jsonl(path, dict_records)
    elif suffix == "html":
        if not result_objects:
            raise ValueError("HTML format requires ResultRecord objects")
        generate_html_report(result_objects, path)
    elif suffix == "sarif":
        if not result_objects:
            raise ValueError("SARIF format requires ResultRecord objects")
        generate_sarif_report(result_objects, path)
    else:
        raise ValueError("Output format must be csv, jsonl, html, or sarif (use --format)")


def build_client(args: argparse.Namespace) -> OllamaClient | LLMProvider | None:
    """Build a provider client based on CLI arguments."""
    if args.demo:
        return None

    try:
        # Use the new provider system
        if args.provider == "ollama":
            # Special handling for Ollama to support legacy --ollama-url
            base_url = args.ollama_url or os.environ.get(BASE_URL_ENV)
            from llm_tester.providers.ollama import OllamaProvider

            return OllamaProvider.from_env(
                timeout=args.timeout,
                debug=args.debug,
                retries=args.retries,
                base_url=base_url,
            )
        else:
            # Use factory for other providers
            return create_provider(
                args.provider,
                timeout=args.timeout,
                debug=args.debug,
                retries=args.retries,
            )
    except ProviderError as exc:
        raise ProviderError(f"Failed to initialize {args.provider} provider: {exc}") from exc


def load_system_prompt(value: str | None) -> str | None:
    """Load system prompt from inline text or file reference (@path)."""
    if value is None:
        return None
    if value.startswith("@"):
        file_path = Path(value[1:])
        if not file_path.exists():
            raise FileNotFoundError(f"System prompt file not found: {file_path}")
        return file_path.read_text(encoding="utf-8").strip()
    return value


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    # Setup logging
    logger = setup_logging(
        level=args.log_level,
        log_file=args.log_file,
        enable_file_logging=bool(args.log_file),
    )

    logger.info("Starting LLM Tester assessment")

    try:
        prompts = prompt_loader.load_prompts(args.prompts_file, args.max_prompts)
        logger.info(f"Loaded {len(prompts)} prompts from {args.prompts_file}")
    except (FileNotFoundError, ValueError) as exc:
        logger.error(f"Error loading prompts: {exc}")
        print(f"Error loading prompts: {exc}", file=sys.stderr)
        return 1

    if not prompts:
        logger.error("No prompts found in file")
        print("No prompts found in file.", file=sys.stderr)
        return 1

    try:
        system_prompt = load_system_prompt(args.system_prompt)
        if system_prompt:
            logger.info("Loaded system prompt")
    except (FileNotFoundError, ValueError) as exc:
        logger.error(f"Error loading system prompt: {exc}")
        print(f"Error loading system prompt: {exc}", file=sys.stderr)
        return 1

    # Load custom rules if specified
    custom_rules = None
    if args.rules_file:
        try:
            custom_rules = load_rules_from_json(args.rules_file)
            logger.info(f"Loaded {len(custom_rules)} custom rules from {args.rules_file}")
        except (FileNotFoundError, ValueError) as exc:
            logger.error(f"Error loading custom rules: {exc}")
            print(f"Error loading custom rules: {exc}", file=sys.stderr)
            return 1

    try:
        client = build_client(args)
        if client:
            logger.info(f"Configured Ollama client (timeout={args.timeout}s, retries={args.retries})")
    except OllamaError as exc:
        logger.error(f"Error configuring Ollama client: {exc}")
        print(f"Error configuring Ollama client: {exc}", file=sys.stderr)
        return 2

    try:
        logger.info(f"Running assessment with {args.workers} worker(s)")
        results = run_assessment(
            prompts,
            args.model,
            client=client,
            demo_mode=args.demo,
            system_prompt=system_prompt,
            rules=custom_rules,
            workers=args.workers,
            show_progress=not args.no_progress,
        )
        logger.info(f"Assessment complete. Processed {len(results)} prompts")
    except OllamaError as exc:
        logger.error(f"Ollama error: {exc}")
        print(f"Ollama error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 4

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        save_output(output_path, serialize_results(results), forced_format=args.format)
        logger.info(f"Results saved to {output_path}")
    except ValueError as exc:
        logger.error(f"Error writing output: {exc}")
        print(f"Error writing output: {exc}", file=sys.stderr)
        return 1

    # Generate HTML report if requested
    if args.html_report:
        try:
            html_path = Path(args.html_report)
            html_path.parent.mkdir(parents=True, exist_ok=True)
            generate_html_report(results, html_path, title=f"LLM Security Assessment - {args.model}")
            logger.info(f"HTML report generated at {html_path}")
            print(f"HTML report generated at {html_path}")
        except Exception as exc:  # pragma: no cover
            logger.error(f"Error generating HTML report: {exc}")
            print(f"Error generating HTML report: {exc}", file=sys.stderr)

    print(f"Processed {len(results)} prompts. Results stored at {output_path}.")
    if total_cost > 0:
        print(f"Total estimated cost: ${total_cost:.4f} USD")

    # Count triggered rules
    total_triggered = sum(1 for r in results if r.triggered_rules)
    if total_triggered > 0:
        print(f"Vulnerabilities detected: {total_triggered}/{len(results)} prompts triggered rules")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
