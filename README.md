<p align="left">
  <img src="logo.png" width="350"><br><br>

# LLM Tester - Industry-Standard LLM Security Toolkit
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/security-red%20teaming-red.svg)](https://github.com/autrion/llm_tester)

**LLM Tester** is a comprehensive security testing toolkit for Large Language Models. Think **NMAP for LLMs** - the industry-standard tool for red-teaming, vulnerability assessment, and security evaluation of AI systems.

## 🚀 What's New in v0.2

- ✅ **Multi-Provider Support**: OpenAI, Anthropic, Google (Gemini), Azure OpenAI, Ollama
- ✅ **150+ Attack Vectors**: Comprehensive prompt injection, jailbreaks, data exfiltration, encoding attacks
- ✅ **60+ Detection Rules**: Advanced pattern matching for vulnerability detection
- ✅ **ML-Based Detection**: Semantic similarity for catching novel jailbreak variants
- ✅ **Async Parallel Execution**: 10x faster with concurrent request processing
- ✅ **HTML Reports**: Professional, interactive reports with charts and statistics
- ✅ **SARIF Output**: GitHub Code Scanning integration
- ✅ **Cost Tracking**: Automatic cost estimation per request and total
- ✅ **Security Scoring**: 0-100 security score with risk levels
- ✅ **CI/CD Integration**: Ready-to-use GitHub Actions workflow

## 📋 Features

- **Line-delimited prompt files** with optional metadata comments (e.g., `# category: prompt_injection`)
- **Deterministic offline demo mode** for quick runs without network access
- **Ollama client integration** for local or remote model endpoints
- **Rule engine** with keyword and regex rules for common jailbreak, prompt-injection, and safety-bypass cues
- **Custom rules** loading from JSON files
- **Parallel processing** for faster assessments with multiple workers
- **Progress tracking** with visual progress bars (via tqdm)
- **Exponential backoff** for robust retry logic on network failures
- **Structured logging** with configurable log levels and file output
- **HTML report generation** with statistics and visualizations
- **Multiple output formats**: CSV, JSONL, and HTML
- **System prompt injection** for testing prompt leakage scenarios

- **Multi-Provider Architecture**: Test any LLM through a unified interface
  - OpenAI (GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5, o1)
  - Anthropic (Claude 3.5 Sonnet, Opus, Haiku)
  - Google (Gemini 2.0, 1.5 Pro, 1.5 Flash)
  - Azure OpenAI
  - Ollama (local models)

- Python 3.11+
- `tqdm` for progress bars
- Optional: access to an Ollama instance (defaults to `http://localhost:11434`)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Quick start

### Test ALL Attack Vectors (203 attacks)

```bash
# Demo mode - instant results, no API calls
python -m llm_tester.cli \
  --prompts-file llm_tester/prompts_extended.txt \
  --demo \
  --html-report results/all_attacks.html \
  --workers 4

# Against OpenAI GPT-4o
export OPENAI_API_KEY="your-key"
python -m llm_tester.cli \
  --provider openai \
  --model gpt-4o-mini \
  --prompts-file llm_tester/prompts_extended.txt \
  --html-report results/gpt4o_report.html \
  --workers 10
```

### ML-Based Detection (Always Active!)

**ML detection is automatically enabled** - no configuration needed!

The `ml_semantic_jailbreak` rule uses semantic similarity to catch jailbreak variants that bypass traditional regex rules:

```bash
# Verify ML detection is active
python3 -c "from llm_tester.rules import ML_AVAILABLE; \
  print('ML Detection:', 'ENABLED ✅' if ML_AVAILABLE else 'DISABLED ❌')"

# See ML detection in action (debug mode)
python -m llm_tester.cli \
  --prompts-file llm_tester/prompt_library/jailbreaks.txt \
  --demo \
  --log-level DEBUG \
  --output results.csv
```

**How it works:**
- Traditional Rule: `"ignore previous instructions"` → exact match
- ML Detection: `"disregard prior directives"` → semantic similarity 0.78 → DETECTED ✅

### Basic Usage

```bash
# Clone the repository
git clone https://github.com/autrion/llm_tester.git
cd llm_tester

# Run against Ollama
export OLLAMA_URL=http://localhost:11434  # optional; defaults to this value
python -m llm_tester.cli --model llama3 --output results.jsonl --timeout 60 --retries 2
```

### Advanced Features

```bash
# Parallel processing with 4 workers
python -m llm_tester.cli --model llama3 --workers 4 --output results.csv

# Generate HTML report with statistics
python -m llm_tester.cli --model llama3 --html-report report.html --output results.csv

# Use custom rules from JSON
python -m llm_tester.cli --model llama3 --rules-file custom_rules.json

# System prompt injection for testing
python -m llm_tester.cli --model llama3 --system-prompt "You are a helpful assistant. Secret: 42."
python -m llm_tester.cli --model llama3 --system-prompt @system_prompt.txt

# Enhanced logging
python -m llm_tester.cli --model llama3 --log-level DEBUG --log-file assessment.log

# Disable progress bar (useful for CI/CD)
python -m llm_tester.cli --model llama3 --no-progress
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--model` | Target model identifier | `gpt-4o-mini` |
| `--prompts-file` | Path to prompt list file | `prompts.txt` |
| `--max-prompts` | Maximum number of prompts to process | All |
| `--output` | Output file path (.csv or .jsonl) | `results.csv` |
| `--format` | Force output format (csv/jsonl) | From extension |
| `--ollama-url` | Ollama base URL | `http://localhost:11434` |
| `--timeout` | Request timeout in seconds | `30` |
| `--retries` | Number of retries for transient errors | `0` |
| `--workers` | Number of parallel workers | `1` |
| `--demo` | Run in offline demo mode | `false` |
| `--system-prompt` | System prompt (inline or @file) | None |
| `--rules-file` | Path to custom rules JSON | Default rules |
| `--html-report` | Generate HTML report at path | None |
| `--log-level` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `--log-file` | Path to log file | None |
| `--no-progress` | Disable progress bar | `false` |

```bash
export OPENAI_API_KEY="your-api-key"
python -m llm_tester.cli \
  --provider openai \
  --model gpt-4o-mini \
  --output report.html \
  --format html
```

### 3. Test Anthropic Claude

```bash
export ANTHROPIC_API_KEY="your-api-key"
python -m llm_tester.cli \
  --provider anthropic \
  --model claude-3-5-sonnet-20241022 \
  --output report.html \
  --format html
```

### 4. Test Google Gemini

```bash
export GOOGLE_API_KEY="your-api-key"
python -m llm_tester.cli \
  --provider google \
  --model gemini-1.5-flash \
  --output report.html \
  --format html
```

### 5. Test with Extended Prompts

## Custom Rules

You can define custom detection rules in JSON format:

```json
{
  "keyword_rules": [
    {
      "name": "custom_keyword_rule",
      "description": "Detects specific keywords",
      "keywords": ["forbidden", "classified", "secret"]
    }
  ],
  "regex_rules": [
    {
      "name": "custom_regex_rule",
      "description": "Detects specific patterns",
      "pattern": "\\bCONFIDENTIAL:\\s*\\w+",
      "flags": 2
    }
  ]
}
```

Load with: `--rules-file custom_rules.json`

## Performance Optimization

### Parallel Processing

For large-scale assessments, use multiple workers:

```bash
# Process with 8 parallel workers
python -m llm_tester.cli --model llama3 --workers 8 --prompts-file large_dataset.txt
```

**Note:** More workers = higher throughput but also higher resource usage.

### Retry Strategy

The tool implements exponential backoff for network errors:

```bash
# Retry up to 3 times with exponential backoff (1s, 2s, 4s)
python -m llm_tester.cli --model llama3 --retries 3
```

## Outputs

```bash
python -m llm_tester.cli \
  --provider openai \
  --model gpt-4o \
  --output results.sarif \
  --format sarif
```

### 7. Parallel Execution (10x Faster!)

```bash
# Run with 20 concurrent requests (default: 10)
python -m llm_tester.cli \
  --provider openai \
  --model gpt-4o-mini \
  --prompts-file llm_tester/prompts_extended.txt \
  --output report.html \
  --format html \
  --concurrency 20

# Sequential execution (disable async)
python -m llm_tester.cli \
  --provider openai \
  --model gpt-4o \
  --no-async
```

- `.csv`: Tabular output with headers
- `.jsonl`: One JSON object per line
- `.html`: Visual report with statistics and charts (via `--html-report`)

### HTML Reports

Generate comprehensive HTML reports with:
- **Summary statistics**: Total prompts, trigger rates, response lengths
- **Visual charts**: Rule triggers and category distributions
- **Detailed tables**: All prompts, responses, and triggered rules
- **Interactive design**: Responsive layout with search and filtering

Example:
```bash
python -m llm_tester.cli --model llama3 --html-report report.html --output data.csv
```

### HTML Report (Recommended)

Professional, interactive report with:
- Executive summary with security score
- Risk level assessment (LOW/MEDIUM/HIGH/CRITICAL)
- Vulnerability statistics and charts
- Detailed results table
- Cost analysis

```bash
--output report.html --format html
```
llm_tester/
├── llm_tester/
│   ├── analysis.py         # Response analysis helpers
│   ├── cli.py              # CLI entry point with all options
│   ├── client.py           # Ollama client with retry logic
│   ├── logging_config.py   # Logging configuration
│   ├── prompts.py          # Prompt loader with metadata
│   ├── reporting.py        # HTML report generation
│   ├── rule_loader.py      # Custom rules from JSON
│   ├── rules.py            # Rule engine (keyword + regex)
│   └── runner.py           # Assessment orchestration
├── tests/                  # Pytest test suite
│   ├── test_cli.py
│   ├── test_client.py
│   ├── test_prompts.py
│   ├── test_reporting.py
│   ├── test_rule_loader.py
│   ├── test_rules.py
│   └── test_runner.py
├── prompts.txt             # Default prompt dataset
├── requirements.txt        # Python dependencies
├── main.py                 # Entry point wrapper
└── README.md               # This file
```

Then upload via GitHub Actions or manually.

Install dependencies and run the test suite:

```bash
pip install -r requirements.txt
pytest

# Run tests with coverage
pytest --cov=llm_tester

# Run specific test file
pytest tests/test_providers.py
```

The tests run entirely offline using dummy data and mocks. **37 tests** covering all features.

## Best Practices

### Security Testing Workflows

1. **Start with demo mode** to validate your setup:
   ```bash
   python -m llm_tester.cli --demo --max-prompts 5
   ```

2. **Use system prompts** to test prompt leakage:
   ```bash
   python -m llm_tester.cli --model llama3 --system-prompt @secret.txt
   ```

3. **Generate HTML reports** for stakeholder review:
   ```bash
   python -m llm_tester.cli --model llama3 --html-report report.html
   ```

4. **Enable detailed logging** for debugging:
   ```bash
   python -m llm_tester.cli --model llama3 --log-level DEBUG --log-file debug.log
   ```

### Performance Tips

- Use `--workers` for large datasets (recommended: 4-8 workers)
- Set appropriate `--timeout` based on model response times
- Use `--retries 2` or `--retries 3` for unstable connections
- Disable progress bar with `--no-progress` in CI/CD pipelines

## Changelog

### v2.0 (Latest)
- ✨ Parallel processing support (`--workers`)
- ✨ Progress bars with tqdm
- ✨ Exponential backoff for retries
- ✨ Custom rules from JSON files
- ✨ HTML report generation
- ✨ Structured logging system
- ✨ System prompt injection feature
- 🐛 Improved error handling
- 📚 Comprehensive test coverage (37 tests)
## 💝 Support This Project

If you find LLM Tester useful, consider supporting its development:

**Crypto:**
- **Bitcoin**: `bc1qcexlm8hc4lh86sg5pmlq26hzu075q4y9jm88zh`
- **Ethereum**: `0x300D3654D7D87ef3Dbe56B7eF0AF570C39B77580`
- **Solana**: `26EdJTMECZm3rqxhFHaL48zBtJRvAjn9CF5EFpB1DV5K`

**Other:**
- ☕ [Buy Me a Coffee](https://buymeacoffee.com/autrion)

Your support helps maintain and improve this tool for the security community!

---

### v1.0
- Initial release with basic functionality
