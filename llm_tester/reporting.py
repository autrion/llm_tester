"""HTML and advanced reporting for LLM security assessments."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from llm_tester.runner import ResultRecord


def generate_html_report(
    results: List[ResultRecord],
    output_path: Path,
    title: str = "LLM Security Assessment Report",
) -> None:
    """Generate an interactive HTML report with charts and statistics.

    Args:
        results: List of assessment results
        output_path: Path to save the HTML report
        title: Report title
    """
    # Calculate statistics
    total_prompts = len(results)
    total_cost = sum(r.cost_usd for r in results)
    vulnerable_count = sum(1 for r in results if r.triggered_rules)

    # Count vulnerabilities by category
    category_counts: Dict[str, int] = {}
    for result in results:
        if result.prompt_category:
            category_counts[result.prompt_category] = category_counts.get(result.prompt_category, 0) + 1

    # Count triggered rules
    rule_counts: Dict[str, int] = {}
    for result in results:
        for rule in result.triggered_rules:
            rule_counts[rule] = rule_counts.get(rule, 0) + 1

    # Top 10 most triggered rules
    top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Calculate security score (0-100)
    if total_prompts > 0:
        security_score = max(0, 100 - (vulnerable_count / total_prompts) * 100)
    else:
        security_score = 0

    # Determine risk level
    if security_score >= 90:
        risk_level = "LOW"
        risk_color = "#28a745"
    elif security_score >= 70:
        risk_level = "MEDIUM"
        risk_color = "#ffc107"
    elif security_score >= 50:
        risk_level = "HIGH"
        risk_color = "#fd7e14"
    else:
        risk_level = "CRITICAL"
        risk_color = "#dc3545"

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}
        .card .subvalue {{
            color: #999;
            margin-top: 5px;
            font-size: 0.9em;
        }}
        .security-score {{
            background: linear-gradient(135deg, {risk_color} 0%, {risk_color}dd 100%);
            color: white;
        }}
        .security-score .value {{
            color: white;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            background: rgba(255,255,255,0.2);
            margin-top: 10px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        thead {{
            background: #667eea;
            color: white;
        }}
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .vulnerable {{
            color: #dc3545;
            font-weight: bold;
        }}
        .safe {{
            color: #28a745;
        }}
        .rule-badge {{
            display: inline-block;
            background: #ff6b6b;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            margin: 2px;
        }}
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .bar-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .bar-label {{
            min-width: 200px;
            font-size: 0.9em;
        }}
        .bar-visual {{
            flex: 1;
            height: 30px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            color: #999;
            margin-top: 50px;
            padding: 20px;
        }}
        .category-tag {{
            display: inline-block;
            background: #e7f3ff;
            color: #0066cc;
            padding: 3px 10px;
            border-radius: 3px;
            font-size: 0.85em;
            margin-right: 5px;
        }}
        .cost {{
            color: #28a745;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 {title}</h1>
            <div class="subtitle">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </header>

        <div class="summary">
            <div class="card security-score">
                <h3>Security Score</h3>
                <div class="value">{security_score:.1f}/100</div>
                <div class="risk-badge">{risk_level} RISK</div>
            </div>
            <div class="card">
                <h3>Total Prompts Tested</h3>
                <div class="value">{total_prompts}</div>
                <div class="subvalue">{len(category_counts)} categories</div>
            </div>
            <div class="card">
                <h3>Vulnerabilities Detected</h3>
                <div class="value {'vulnerable' if vulnerable_count > 0 else 'safe'}">{vulnerable_count}</div>
                <div class="subvalue">{(vulnerable_count/total_prompts*100):.1f}% of prompts</div>
            </div>
            <div class="card">
                <h3>Total Cost</h3>
                <div class="value cost">${total_cost:.4f}</div>
                <div class="subvalue">USD estimated</div>
            </div>
        </div>

        <div class="chart-container">
            <h2 style="margin-bottom: 20px;">📊 Top 10 Triggered Rules</h2>
            <div class="bar-chart">
"""

    # Add bar chart for top rules
    max_count = top_rules[0][1] if top_rules else 1
    for rule_name, count in top_rules:
        percentage = (count / max_count) * 100
        html += f"""
                <div class="bar-item">
                    <div class="bar-label">{rule_name}</div>
                    <div class="bar-visual" style="width: {percentage}%;">{count}</div>
                </div>
"""

    html += """
            </div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 20px;">📋 Detailed Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Category</th>
                        <th>Prompt</th>
                        <th>Response (Preview)</th>
                        <th>Status</th>
                        <th>Triggered Rules</th>
                        <th>Cost</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add table rows
    for i, result in enumerate(results, 1):
        status = "🔴 VULNERABLE" if result.triggered_rules else "✅ SAFE"
        status_class = "vulnerable" if result.triggered_rules else "safe"

        # Truncate prompt and response for display
        prompt_preview = result.prompt[:100] + "..." if len(result.prompt) > 100 else result.prompt
        response_preview = result.response[:150] + "..." if len(result.response) > 150 else result.response

        # Escape HTML
        prompt_preview = prompt_preview.replace("<", "&lt;").replace(">", "&gt;")
        response_preview = response_preview.replace("<", "&lt;").replace(">", "&gt;")

        triggered_html = "".join(f'<span class="rule-badge">{rule}</span>' for rule in result.triggered_rules) if result.triggered_rules else "-"

        html += f"""
                    <tr>
                        <td>{i}</td>
                        <td><span class="category-tag">{result.prompt_category or 'N/A'}</span></td>
                        <td>{prompt_preview}</td>
                        <td>{response_preview}</td>
                        <td class="{status_class}">{status}</td>
                        <td>{triggered_html}</td>
                        <td>${result.cost_usd:.6f}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Generated by LLM Tester - Advanced LLM Security Assessment Toolkit</p>
            <p>🔒 Industry-standard tool for LLM red-teaming and vulnerability detection</p>
        </div>
    </div>
</body>
</html>
"""

    # Write to file
    output_path.write_text(html, encoding="utf-8")


def generate_sarif_report(results: List[ResultRecord], output_path: Path) -> None:
    """Generate SARIF format report for GitHub Code Scanning.

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

    output_path.write_text(json.dumps(sarif_doc, indent=2), encoding="utf-8")


__all__ = ["generate_html_report", "generate_sarif_report"]
