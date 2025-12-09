# LLM Tester (AI Security Toolkit)

LLM Tester is a lightweight command-line utility for running high-risk prompts through a Large Language Model and collecting simple security signals. It is intentionally minimal: the current version operates entirely offline by default, producing deterministic demo responses so you can exercise the pipeline without network access. When credentials are provided, it connects to an AnythingLLM instance so you can route prompts to any model configured there.

## Project status
- **Current behavior:** Loads prompts from a text file, optionally forwards them to AnythingLLM for real model responses, scans for basic red-flag keywords, and writes results to CSV or JSONL.
- **LLM calls:** Uses AnythingLLM as the default provider when an API key is present. Falls back to deterministic demo responses when demo mode is enabled or credentials are missing.
- **Scope:** Useful for exercising a red-team style workflow skeleton; not a full evaluator.

## Features
- Reads prompts from `prompts.json` (structured objects with `id`, `category`, `severity`, and `prompt`).
- Deterministic demo mode when no API key is set or when `LLM_TESTER_DEMO` is enabled.
- Sends prompts to AnythingLLM when configured, enabling quick testing of any connected model.
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

Use `--max-prompts` to limit how many prompts from `prompts.json` are processed and `--prompts-file` to point to a custom list. Provide AnythingLLM credentials to get real model outputs instead of demo responses.

## Configuration
- `ANYTHINGLLM_API_KEY`: API key for your AnythingLLM instance.
- `ANYTHINGLLM_URL`: Base URL to your AnythingLLM server (defaults to `http://localhost:3001`).
- `ANYTHINGLLM_WORKSPACE`: Workspace slug to target (defaults to `default`).
- `LLM_TESTER_DEMO`: When set to any value, forces deterministic demo responses even if an API key is present.

Example configuration for running against AnythingLLM:

```bash
export ANYTHINGLLM_API_KEY=your_token_here
export ANYTHINGLLM_URL=https://anythingllm.example.com
export ANYTHINGLLM_WORKSPACE=red-team
python main.py --output results.jsonl --model mistral-small-latest
```

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
`prompts.json` contains an array of prompt objects with the following fields:

- `id`: Unique identifier for the prompt.
- `category`: Category such as `prompt_injection`.
- `severity`: Risk level (e.g., `high`).
- `prompt`: The actual prompt text to send to the model.

Update this file to target scenarios such as prompt injection, system prompt leakage, jailbreaking, or malicious code generation.

## Project structure
```
llm_tester/
├── main.py      # CLI entry point and analysis logic
├── anythingllm_client.py  # Minimal AnythingLLM HTTP client
├── prompts.json  # Default high-risk prompt list
└── README.md    # Project documentation
```

## Roadmap (high level)
- Harden the AnythingLLM integration (streaming, retries, richer error handling).
- Expand analysis rules beyond basic keyword scans.
- Add scoring, logging improvements, and richer reporting.
- Package as a reusable module or CLI tool.

## License
Licensed under the MIT License. See [LICENSE](LICENSE) for details.
