"""
LLM Tester - Day 1

This script loads a list of high-risk prompts from `prompts.txt`
and prints them to the console.

The goal for Day 1 is to establish the project structure, verify
basic file handling, and prepare the foundation for future AI
security tests (prompt injection, jailbreak attempts, etc.).

Author: Roland Mitterbauer
License: GNU AGPLv3
"""

from pathlib import Path


def load_prompts(file_path: str) -> list[str]:
    """
    Load prompts from a text file.

    Each non-empty line is treated as a separate prompt.
    The function returns a list of strings.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    prompts: list[str] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            clean = line.strip()
            if clean:
                prompts.append(clean)

    return prompts


def main() -> None:
    """
    Entry point of the LLM tester.

    Day 1 behavior:
    - Load prompts from `prompts.txt`
    - Print them with indexing
    """
    prompts = load_prompts("prompts.txt")

    print("=== LLM Tester (Day 1) ===")
    print(f"Loaded {len(prompts)} prompts:")
    print("---------------------------")

    for index, prompt in enumerate(prompts, start=1):
        print(f"{index}. {prompt}")


if __name__ == "__main__":
    main()
