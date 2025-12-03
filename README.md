# LLM Tester (AI Security Toolkit)

LLM Tester is a lightweight command-line utility for running high-risk prompts through a Large Language Model and collecting simple security signals. It is intentionally minimal: the current version operates entirely offline by default, producing deterministic demo responses so you can exercise the pipeline without network access.

## Project status
- **Current behavior:** Loads prompts from a text file, generates demo responses, scans for basic red-flag keywords, and writes results to CSV or JSONL.
- **LLM calls:** A real LLM API integration is **not implemented yet**. Setting an API key without demo mode enabled will raise a `NotImplementedError`.
- **Scope:** Useful for exercising a red-team style workflow skeleton; not a full evaluator.

## Features
- Reads prompts from `prompts.txt` (ignores blank lines and lines starting with `#`).
- Deterministic demo mode when no API key is set or when `LLM_TESTER_DEMO` is enabled.
- Simple response analysis that flags risky keywords (e.g., `hack`, `bypass`, `jailbreak`).
- Outputs structured results as `.csv` or `.jsonl` with timestamps and metrics.
- Pure standard-library Python; no extra dependencies required.

## Prerequisites
- Python 3.10+
- A shell environment to run `python main.py`

## Quick start
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/llm_tester
cd llm_tester

# Run in demo mode (offline)
export LLM_TESTER_DEMO=1
python main.py --output results.csv
```

Use `--max-prompts` to limit how many prompts from `prompts.txt` are processed and `--prompts-file` to point to a custom list.

## Configuration
- `LLM_API_KEY`: Placeholder for a future real provider key. Currently unused; real API calls are not implemented.
- `LLM_TESTER_DEMO`: When set to any value, forces deterministic demo responses even if an API key is present.

## Outputs
Each processed prompt produces a record with:
- `timestamp`: UTC ISO 8601 timestamp
- `prompt`: The input prompt text
- `model`: The model name passed via `--model`
- `response`: The (demo) model response
- `response_length`: Character count of the response
- `red_flags`: List of matched risky keywords
- `contains_red_flags`: Boolean indicator derived from `red_flags`

Choose an output format with the file extension:
- `.csv`: Tabular output with headers
- `.jsonl`: One JSON object per line

## Prompts file format
`prompts.txt` contains one prompt per line. Lines that are blank or begin with `#` are skipped. Customize this file to target scenarios such as prompt injection, system prompt leakage, jailbreaking, or malicious code generation.

## Project structure
```
llm_tester/
├── main.py      # CLI entry point and analysis logic
├── prompts.txt  # Default high-risk prompt list
└── README.md    # Project documentation
```

## Roadmap (high level)
- Wire up a real LLM provider client using `LLM_API_KEY`.
- Expand analysis rules beyond basic keyword scans.
- Add scoring, logging improvements, and richer reporting.
- Package as a reusable module or CLI tool.

## License
Licensed under the MIT License. See [LICENSE](LICENSE) for details.
