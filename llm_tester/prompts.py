"""Prompt loading utilities.

Each non-empty line in a prompt file represents a single scenario. Lines that
start with ``#`` are treated as comments and ignored. Comment lines may also
include metadata such as ``# category: prompt_injection`` which is applied to
subsequent prompts until another metadata block overrides it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class Prompt:
    """Represents a single test scenario."""

    text: str
    category: str | None = None
    metadata: Dict[str, str] = field(default_factory=dict)


def _parse_metadata(comment_line: str) -> dict[str, str]:
    content = comment_line.lstrip("#").strip()
    if not content:
        return {}
    if ":" not in content:
        return {}
    key, _, value = content.partition(":")
    return {key.strip().lower(): value.strip()}


def load_prompts(path: str | Path, max_prompts: int | None = None) -> List[Prompt]:
    """Load prompts from a line-delimited file with optional metadata comments."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    prompts: List[Prompt] = []
    current_metadata: dict[str, str] = {}

    with file_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                metadata_update = _parse_metadata(line)
                if metadata_update:
                    current_metadata.update(metadata_update)
                continue

            metadata = dict(current_metadata)
            prompt = Prompt(
                text=line,
                category=metadata.get("category"),
                metadata=metadata,
            )
            prompts.append(prompt)

            if max_prompts is not None and len(prompts) >= max_prompts:
                break

    return prompts


__all__ = ["Prompt", "load_prompts"]
