import tempfile
from pathlib import Path

from llm_tester.reporting import generate_html_report, generate_statistics
from llm_tester.runner import ResultRecord


def test_generate_statistics() -> None:
    records = [
        ResultRecord(
            timestamp="2024-01-01T12:00:00Z",
            prompt="Test prompt 1",
            prompt_category="test",
            response="Response 1",
            model="test-model",
            response_length=10,
            triggered_rules=["rule1"],
        ),
        ResultRecord(
            timestamp="2024-01-01T12:00:01Z",
            prompt="Test prompt 2",
            prompt_category="test",
            response="Response 2",
            model="test-model",
            response_length=20,
            triggered_rules=[],
        ),
    ]

    stats = generate_statistics(records)

    assert stats["total_prompts"] == 2
    assert stats["triggered_count"] == 1
    assert stats["trigger_rate"] == 50.0
    assert stats["avg_response_length"] == 15.0
    assert "test" in stats["categories"]


def test_generate_html_report() -> None:
    records = [
        ResultRecord(
            timestamp="2024-01-01T12:00:00Z",
            prompt="Test prompt",
            prompt_category="test",
            response="Test response",
            model="test-model",
            response_length=13,
            triggered_rules=["test_rule"],
        ),
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as f:
        temp_path = f.name

    try:
        generate_html_report(records, temp_path, title="Test Report")

        # Verify file was created
        assert Path(temp_path).exists()

        # Check content contains expected elements
        content = Path(temp_path).read_text()
        assert "Test Report" in content
        assert "Test prompt" in content
        assert "test_rule" in content
        assert "<!DOCTYPE html>" in content
    finally:
        Path(temp_path).unlink()


def test_generate_statistics_empty() -> None:
    stats = generate_statistics([])
    assert stats == {}
