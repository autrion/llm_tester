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
from llm_tester.client import (
    API_KEY_ENV,
    BASE_URL_ENV,
    WORKSPACE_ENV,
    AnythingLLMClient,
    AnythingLLMError,
)
from llm_tester.runner import DEMO_ENV, ResultRecord, run_assessment, serialize_results


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run security prompts against an LLM endpoint.")
    parser.add_argument("--model", default="gpt-4o-mini", help="Target model identifier.")
    parser.add_argument("--prompts-file", default="prompts.txt", help="Path to the prompt list file.")
    parser.add_argument("--max-prompts", type=int, default=None, help="Maximum number of prompts to process.")
    parser.add_argument("--output", default="results.csv", help="Output file path (.csv or .jsonl).")
    parser.add_argument("--api-key", default=None, help="AnythingLLM API key (overrides env).")
    parser.add_argument("--anythingllm-url", default=None, help="AnythingLLM base URL (overrides env).")
    parser.add_argument("--workspace", default=None, help="AnythingLLM workspace slug (overrides env).")
    parser.add_argument("--demo", action="store_true", help="Run in offline demo mode without network calls.")
    parser.add_argument("--format", choices=["csv", "jsonl"], default=None, help="Force output format.")
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


def save_output(path: Path, records: Iterable[dict], forced_format: str | None = None) -> None:
    suffix = forced_format or path.suffix.lstrip(".").lower()
    if suffix == "csv":
        _write_csv(path, records)
    elif suffix == "jsonl":
        _write_jsonl(path, records)
    else:
        raise ValueError("Output must be .csv or .jsonl or use --format")


def build_client(args: argparse.Namespace) -> AnythingLLMClient | None:
    api_key = args.api_key or os.environ.get(API_KEY_ENV)
    if args.demo or not api_key:
        return None

    base_url = args.anythingllm_url or os.environ.get(BASE_URL_ENV)
    workspace = args.workspace or os.environ.get(WORKSPACE_ENV)
    os.environ.setdefault(BASE_URL_ENV, base_url or "")
    os.environ.setdefault(WORKSPACE_ENV, workspace or "")
    os.environ.setdefault(API_KEY_ENV, api_key)

    return AnythingLLMClient.from_env()


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        prompts = prompt_loader.load_prompts(args.prompts_file, args.max_prompts)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading prompts: {exc}", file=sys.stderr)
        return 1

    if not prompts:
        print("No prompts found in file.", file=sys.stderr)
        return 1

    try:
        client = build_client(args)
    except AnythingLLMError as exc:
        print(f"Error configuring AnythingLLM client: {exc}", file=sys.stderr)
        return 2

    try:
        results = run_assessment(prompts, args.model, client=client, demo_mode=args.demo)
    except AnythingLLMError as exc:
        print(f"AnythingLLM error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 4

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        save_output(output_path, serialize_results(results), forced_format=args.format)
    except ValueError as exc:
        print(f"Error writing output: {exc}", file=sys.stderr)
        return 1

    print(f"Processed {len(results)} prompts. Results stored at {output_path}.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
