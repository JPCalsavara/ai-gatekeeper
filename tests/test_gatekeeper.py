import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import gatekeeper
from gatekeeper import (
    ReviewState,
    AgentMetric,
    run_agent,
    code_review_node,
    supervisor_node,
    build_graph,
    generate_report,
    PRICING,
)

# Alias to prevent pytest from treating the gatekeeper node as a test case
diagnose_tests_node = gatekeeper.test_diagnostics_node

def test_pricing_keys_exist():
    """Validates that pricing models and keys are defined."""
    assert "flash" in PRICING
    assert "pro" in PRICING
    assert PRICING["flash"]["name"] == "gemini-2.5-flash"
    assert PRICING["pro"]["name"] == "gemini-2.5-pro"

def test_run_agent_telemetry_calculation(mock_flash_response):
    """Verifies that run_agent calculates tokens, duration, and cost accurately."""
    mock_llm = MagicMock()
    mock_resp = mock_flash_response("Test analysis completed", in_tokens=1_000_000, out_tokens=1_000_000)
    mock_llm.invoke.return_value = mock_resp

    content, metric = run_agent(mock_llm, "flash", [])

    assert content == "Test analysis completed"
    assert metric["model"] == "gemini-2.5-flash"
    assert metric["in_tokens"] == 1_000_000
    assert metric["out_tokens"] == 1_000_000
    # in: 0.075, out: 0.30 -> total = 0.375 USD
    assert pytest.approx(metric["cost_usd"], 0.0001) == 0.375
    assert metric["duration_s"] >= 0.0

def test_test_diagnostics_node_when_tests_pass():
    """When tests pass, the node should return immediately without calling LLM (zero cost)."""
    state: ReviewState = {
        "pr_diff": "diff content",
        "harness_rules": "rules content",
        "test_logs": "4 passed in 0.42s",
        "telemetry": {}
    }

    result = diagnose_tests_node(state)

    assert "[PASSED] All tests passed with no errors." in result["test_analysis"]
    assert "telemetry" not in result

def test_test_diagnostics_node_when_tests_fail():
    """When tests fail, it should invoke Flash LLM and record telemetry."""
    state: ReviewState = {
        "pr_diff": "line 15: assert ratio == 0",
        "harness_rules": "rules content",
        "test_logs": "FAILED tests/test_calc.py::test_divide - ZeroDivisionError",
        "telemetry": {}
    }

    mock_metric: AgentMetric = {
        "model": "gemini-2.5-flash",
        "in_tokens": 150,
        "out_tokens": 50,
        "duration_s": 0.3,
        "cost_usd": 0.00003
    }

    with patch("gatekeeper.run_agent", return_value=("Failure at line 15.", mock_metric)) as mock_run:
        result = diagnose_tests_node(state)
        assert mock_run.called
        assert "Failure at line 15." in result["test_analysis"]
        assert "tests" in result["telemetry"]
        assert result["telemetry"]["tests"]["model"] == "gemini-2.5-flash"

def test_code_review_node():
    """Tests code review node checking diff against guidelines."""
    state: ReviewState = {
        "pr_diff": "query = f'SELECT * FROM users WHERE id = {user_id}'",
        "harness_rules": "Never concatenate SQL strings (BLOCKER)",
        "test_logs": "4 passed",
        "telemetry": {}
    }

    mock_metric: AgentMetric = {
        "model": "gemini-2.5-flash",
        "in_tokens": 200,
        "out_tokens": 80,
        "duration_s": 0.4,
        "cost_usd": 0.00004
    }

    with patch("gatekeeper.run_agent", return_value=("BLOCKER: SQL Injection detected.", mock_metric)):
        result = code_review_node(state)

    assert "BLOCKER" in result["code_review"]
    assert "review" in result["telemetry"]

def test_supervisor_node():
    """Tests supervisor node generating final verdict with Gemini Pro."""
    state: ReviewState = {
        "pr_diff": "diff",
        "harness_rules": "rules",
        "test_logs": "logs",
        "test_analysis": "Tests passed",
        "code_review": "BLOCKER detected",
        "telemetry": {
            "review": {
                "model": "gemini-2.5-flash",
                "in_tokens": 100,
                "out_tokens": 50,
                "duration_s": 0.5,
                "cost_usd": 0.0001
            }
        }
    }

    mock_metric: AgentMetric = {
        "model": "gemini-2.5-pro",
        "in_tokens": 400,
        "out_tokens": 120,
        "duration_s": 0.9,
        "cost_usd": 0.0011
    }

    with patch("gatekeeper.run_agent", return_value=("REJECTED: Critical guideline violation.", mock_metric)):
        result = supervisor_node(state)

    assert "REJECTED" in result["final_verdict"]
    assert "supervisor" in result["telemetry"]

def test_full_graph_execution():
    """Executes compiled LangGraph end-to-end to verify parallel fan-out telemetry merging."""
    app = build_graph()

    initial_state = {
        "pr_diff": "sample diff",
        "harness_rules": "sample rules",
        "test_logs": "FAILED test_auth",
        "telemetry": {}
    }

    def mock_run_agent_side_effect(llm, tier, messages):
        tier_name = PRICING[tier]["name"]
        metric: AgentMetric = {
            "model": tier_name,
            "in_tokens": 100,
            "out_tokens": 50,
            "duration_s": 0.2,
            "cost_usd": 0.0001
        }
        if tier == "flash":
            return "Diagnostics or Review Flash result", metric
        return "VERDICT: REJECTED", metric

    with patch("gatekeeper.run_agent", side_effect=mock_run_agent_side_effect):
        result = app.invoke(initial_state)

    assert result["final_verdict"] == "VERDICT: REJECTED"
    assert "tests" in result["telemetry"]
    assert "review" in result["telemetry"]
    assert "supervisor" in result["telemetry"]

def test_generate_report_formatting():
    """Validates markdown report generation and totals calculation without emojis."""
    sample_result: ReviewState = {
        "pr_diff": "diff",
        "harness_rules": "rules",
        "test_logs": "logs",
        "test_analysis": "[PASSED] All tests passed with no errors.",
        "code_review": "No guideline violations found.",
        "final_verdict": "APPROVED",
        "telemetry": {
            "review": {
                "model": "gemini-2.5-flash",
                "in_tokens": 500,
                "out_tokens": 100,
                "duration_s": 1.2,
                "cost_usd": 0.00007
            },
            "supervisor": {
                "model": "gemini-2.5-pro",
                "in_tokens": 1000,
                "out_tokens": 200,
                "duration_s": 2.1,
                "cost_usd": 0.00225
            }
        }
    }

    report = generate_report(sample_result)

    assert "## AI Quality Gatekeeper Report" in report
    assert "APPROVED" in report
    assert "gemini-2.5-flash" in report
    assert "gemini-2.5-pro" in report
    assert "TOTAL" in report
    assert "$0.00232 USD" in report or "0.00232" in report
