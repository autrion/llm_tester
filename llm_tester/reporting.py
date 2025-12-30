"""HTML and statistical reporting for LLM assessment results."""
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from llm_tester.runner import ResultRecord


def generate_statistics(records: Iterable[ResultRecord]) -> Dict[str, any]:
    """Generate statistical summary of assessment results.

    Args:
        records: Assessment result records

    Returns:
        Dictionary containing statistics
    """
    records_list = list(records)
    if not records_list:
        return {}

    total_prompts = len(records_list)
    triggered_count = sum(1 for r in records_list if r.triggered_rules)

    # Count by category
    categories: Dict[str, int] = {}
    for record in records_list:
        cat = record.prompt_category or "uncategorized"
        categories[cat] = categories.get(cat, 0) + 1

    # Count triggered rules
    rule_triggers: Dict[str, int] = {}
    for record in records_list:
        for rule_name in record.triggered_rules:
            rule_triggers[rule_name] = rule_triggers.get(rule_name, 0) + 1

    # Response length stats
    lengths = [r.response_length for r in records_list]
    avg_length = sum(lengths) / len(lengths) if lengths else 0

    return {
        "total_prompts": total_prompts,
        "triggered_count": triggered_count,
        "trigger_rate": (triggered_count / total_prompts * 100) if total_prompts else 0,
        "categories": categories,
        "rule_triggers": rule_triggers,
        "avg_response_length": avg_length,
        "min_response_length": min(lengths) if lengths else 0,
        "max_response_length": max(lengths) if lengths else 0,
    }


def generate_html_report(
    records: Iterable[ResultRecord],
    output_path: str | Path,
    title: str = "LLM Security Assessment Report",
) -> None:
    """Generate an HTML report from assessment results.

    Args:
        records: Assessment result records
        output_path: Path to save HTML file
        title: Report title
    """
    records_list = list(records)
    stats = generate_statistics(records_list)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .results-table {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
        .triggered {{
            background-color: #fff3cd;
        }}
        .rule-badge {{
            display: inline-block;
            background-color: #dc3545;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            margin: 2px;
        }}
        .category-badge {{
            display: inline-block;
            background-color: #6c757d;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        .prompt-text {{
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .response-preview {{
            max-width: 500px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #666;
        }}
        .chart-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .bar {{
            background-color: #667eea;
            height: 25px;
            margin: 5px 0;
            border-radius: 4px;
            position: relative;
            min-width: 2px;
        }}
        .bar-label {{
            display: inline-block;
            min-width: 150px;
            font-weight: 500;
        }}
        .bar-count {{
            position: absolute;
            right: 10px;
            color: white;
            font-weight: bold;
            line-height: 25px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{html.escape(title)}</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats.get('total_prompts', 0)}</div>
            <div class="stat-label">Total Prompts Tested</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.get('triggered_count', 0)}</div>
            <div class="stat-label">Rules Triggered</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.get('trigger_rate', 0):.1f}%</div>
            <div class="stat-label">Trigger Rate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{int(stats.get('avg_response_length', 0))}</div>
            <div class="stat-label">Avg Response Length</div>
        </div>
    </div>

    <div class="chart-section">
        <h2>Rule Triggers</h2>
        {_generate_bar_chart(stats.get('rule_triggers', {}))}
    </div>

    <div class="chart-section">
        <h2>Prompts by Category</h2>
        {_generate_bar_chart(stats.get('categories', {}))}
    </div>

    <div class="results-table">
        <h2 style="padding: 20px 20px 0 20px;">Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Category</th>
                    <th>Prompt</th>
                    <th>Response Preview</th>
                    <th>Triggered Rules</th>
                </tr>
            </thead>
            <tbody>
"""

    # Add rows for each result
    for record in records_list:
        row_class = "triggered" if record.triggered_rules else ""
        prompt_preview = html.escape(record.prompt[:100] + "..." if len(record.prompt) > 100 else record.prompt)
        response_preview = html.escape(
            record.response[:150] + "..." if len(record.response) > 150 else record.response
        )
        category = html.escape(record.prompt_category or "N/A")
        timestamp = record.timestamp.split("T")[1][:8] if "T" in record.timestamp else record.timestamp[:8]

        rules_html = "".join(
            f'<span class="rule-badge">{html.escape(rule)}</span>' for rule in record.triggered_rules
        )

        html_content += f"""
                <tr class="{row_class}">
                    <td>{timestamp}</td>
                    <td><span class="category-badge">{category}</span></td>
                    <td class="prompt-text" title="{html.escape(record.prompt)}">{prompt_preview}</td>
                    <td class="response-preview" title="{html.escape(record.response)}">{response_preview}</td>
                    <td>{rules_html or "—"}</td>
                </tr>
"""

    html_content += """
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>Generated by LLM Tester - AI Security Toolkit</p>
    </div>
</body>
</html>
"""

    Path(output_path).write_text(html_content, encoding="utf-8")


def _generate_bar_chart(data: Dict[str, int]) -> str:
    """Generate HTML for a simple bar chart."""
    if not data:
        return "<p>No data available</p>"

    Args:
        results: List of assessment results
        output_path: Path to save the SARIF report
    """
    sarif_results = []

    for i, result in enumerate(results):
        if result.triggered_rules:
            for rule in result.triggered_rules:
                sarif_results.append({
                    "ruleId": rule,
                    "level": "warning",
                    "message": {
                        "text": f"LLM vulnerability detected: {rule}",
                    },
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": "llm_assessment",
                            },
                            "region": {
                                "startLine": i + 1,
                                "snippet": {
                                    "text": result.prompt[:200]
                                }
                            }
                        }
                    }]
                })

    sarif_doc = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "LLM Tester",
                    "version": "0.2.0",
                    "informationUri": "https://github.com/autrion/llm_tester",
                    "rules": [
                        {
                            "id": rule_id,
                            "name": rule_id,
                            "shortDescription": {
                                "text": f"LLM Security Rule: {rule_id}"
                            },
                            "help": {
                                "text": "Model exhibited behavior matching this security pattern"
                            }
                        }
                        for rule_id in set(r["ruleId"] for r in sarif_results)
                    ]
                }
            },
            "results": sarif_results
        }]
    }

    return "\n".join(html_parts)


__all__ = ["generate_html_report", "generate_statistics"]
