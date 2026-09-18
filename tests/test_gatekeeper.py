import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import gatekeeper
from gatekeeper import (
    ReviewState,
    AgentMetric,
    run_agent,
    code_review_node,
    sonar_triage_node,
    supervisor_node,
    build_graph,
    generate_report,
    PRICING,
)
from sonar_adapter import parse_sonar_json, parse_sarif_json, get_sonar_report
from context_harness import cosine_similarity, chunk_markdown

# Alias to prevent pytest from treating the gatekeeper node as a test case
diagnose_tests_node = gatekeeper.test_diagnostics_node

def test_pricing_keys_exist():
    """Validates that pricing models and keys are defined."""
    assert "flash" in PRICING
    assert "pro" in PRICING
    assert "name" in PRICING["flash"]
    assert "name" in PRICING["pro"]

def test_run_agent_telemetry_calculation(mock_flash_response):
    """Verifies that run_agent calculates tokens, duration, and cost accurately."""
    mock_llm = MagicMock()
    mock_resp = mock_flash_response("Test analysis completed", in_tokens=1_000_000, out_tokens=1_000_000)
    mock_llm.invoke.return_value = mock_resp

    content, metric = run_agent(mock_llm, "flash", [])

    assert content == "Test analysis completed"
    assert metric["model"] == PRICING["flash"]["name"]
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
        "sonar_issues": "",
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
        "sonar_issues": "",
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
        "sonar_issues": "",
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

def test_sonar_triage_node_when_no_issues():
    """When no SonarQube issues exist, skips LLM call with zero cost."""
    state: ReviewState = {
        "pr_diff": "diff",
        "harness_rules": "rules",
        "test_logs": "logs",
        "sonar_issues": "",
        "telemetry": {}
    }

    result = sonar_triage_node(state)
    assert "[PASSED] No SonarQube issues detected." in result["sonar_analysis"]
    assert "telemetry" not in result

def test_sonar_triage_node_with_issues():
    """When SonarQube issues exist, triages them with Flash LLM."""
    state: ReviewState = {
        "pr_diff": "query = f'SELECT * FROM users'",
        "harness_rules": "rules",
        "test_logs": "logs",
        "sonar_issues": "SonarQube detected 1 issue(s):\n- [BLOCKER] services/user_service.py:14 - python:S2077: SQL injection",
        "telemetry": {}
    }

    mock_metric: AgentMetric = {
        "model": "gemini-2.5-flash",
        "in_tokens": 300,
        "out_tokens": 90,
        "duration_s": 0.5,
        "cost_usd": 0.00005
    }

    with patch("gatekeeper.run_agent", return_value=("BLOCKER remediation: use parameterized queries.", mock_metric)):
        result = sonar_triage_node(state)

    assert "BLOCKER remediation" in result["sonar_analysis"]
    assert "sonar" in result["telemetry"]

def test_sonar_adapter_parsing():
    """Tests parsing of SonarQube JSON export."""
    fixture_path = Path("tests/fixtures/sonar_report.json")
    issues = parse_sonar_json(fixture_path)
    assert len(issues) == 2
    assert issues[0].rule == "python:S2077"
    assert issues[0].severity == "BLOCKER"
    assert issues[0].file_path == "services/user_service.py"

def test_context_harness_cosine_similarity():
    """Tests vector math for cosine similarity."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]

    assert pytest.approx(cosine_similarity(v1, v2), 0.0001) == 1.0
    assert pytest.approx(cosine_similarity(v1, v3), 0.0001) == 0.0

def test_supervisor_node():
    """Tests supervisor node generating final verdict with Gemini Pro."""
    state: ReviewState = {
        "pr_diff": "diff",
        "harness_rules": "rules",
        "test_logs": "logs",
        "sonar_issues": "issues",
        "test_analysis": "Tests passed",
        "code_review": "BLOCKER detected",
        "sonar_analysis": "Vulnerability identified",
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

    with patch("gatekeeper.run_agent", return_value=("REJECTED: Critical guideline violation and Sonar blocker.", mock_metric)):
        result = supervisor_node(state)

    assert "REJECTED" in result["final_verdict"]
    assert "supervisor" in result["telemetry"]

def test_full_graph_execution():
    """Executes compiled LangGraph end-to-end to verify 3 parallel fan-out nodes merging telemetry."""
    app = build_graph()

    initial_state = {
        "pr_diff": "sample diff",
        "harness_rules": "sample rules",
        "test_logs": "FAILED test_auth",
        "sonar_issues": "Sonar issues detected",
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
    assert "sonar" in result["telemetry"]
    assert "supervisor" in result["telemetry"]

def test_generate_report_formatting():
    """Validates markdown report generation including SonarQube section without emojis."""
    sample_result: ReviewState = {
        "pr_diff": "diff",
        "harness_rules": "rules",
        "test_logs": "logs",
        "sonar_issues": "issues",
        "test_analysis": "[PASSED] All tests passed with no errors.",
        "code_review": "No guideline violations found.",
        "sonar_analysis": "Identified 1 SQL injection vulnerability. Suggested parameterized query fix.",
        "final_verdict": "APPROVED WITH WARNINGS",
        "telemetry": {
            "review": {
                "model": "gemini-2.5-flash",
                "in_tokens": 500,
                "out_tokens": 100,
                "duration_s": 1.2,
                "cost_usd": 0.00007
            },
            "sonar": {
                "model": "gemini-2.5-flash",
                "in_tokens": 400,
                "out_tokens": 80,
                "duration_s": 0.8,
                "cost_usd": 0.00005
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
    assert "APPROVED WITH WARNINGS" in report
    assert "SonarQube Triage Findings" in report
    assert "gemini-2.5-flash" in report
    assert "gemini-2.5-pro" in report
    assert "TOTAL" in report

def test_clean_diff_filters_lockfiles():
    """Verifies that high-noise lockfiles are filtered out while source code is preserved."""
    from gatekeeper import clean_diff
    raw_diff = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,3 @@
-print("old")
+print("new")
diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,5 +1,5 @@
-"version": "1.0.0"
+"version": "1.0.1"
"""
    cleaned = clean_diff(raw_diff)
    assert "src/app.py" in cleaned
    assert "print(\"new\")" in cleaned
    assert "[IGNORED NOISY FILE: package-lock.json]" in cleaned
    assert '"version": "1.0.1"' not in cleaned

def test_clean_diff_truncates_large_diff():
    """Verifies that diffs exceeding max_chars budget are truncated gracefully."""
    from gatekeeper import clean_diff
    large_diff = "diff --git a/big.py b/big.py\n" + ("x" * 2000)
    cleaned = clean_diff(large_diff, max_chars=500)
    assert len(cleaned) <= 650
    assert "[DIFF TRUNCATED:" in cleaned

def test_diff_aware_sonar_filtering(tmp_path):
    """Verifies that SonarQube issues in untouched files are ignored."""
    from sonar_adapter import get_sonar_report
    import json

    report_file = tmp_path / "sonar-report.json"
    report_file.write_text(json.dumps({
        "total": 2,
        "issues": [
            {
                "key": "AY123456",
                "rule": "python:S2077",
                "severity": "BLOCKER",
                "component": "ai-gatekeeper:services/user_service.py",
                "line": 14,
                "message": "Formatting SQL queries is security-sensitive.",
                "type": "VULNERABILITY"
            },
            {
                "key": "AY123457",
                "rule": "python:S112",
                "severity": "MAJOR",
                "component": "ai-gatekeeper:controllers/payment_controller.py",
                "line": 17,
                "message": "Do not raise generic exceptions.",
                "type": "CODE_SMELL"
            }
        ]
    }))

    # 1. When diff touches services/user_service.py -> only user_service issue is reported
    diff_touching_user = """diff --git a/services/user_service.py b/services/user_service.py
+++ b/services/user_service.py
@@ -1,1 +1,1 @@
"""
    report_touched = get_sonar_report(tmp_path, diff_touching_user)
    assert "services/user_service.py" in report_touched
    assert "controllers/payment_controller.py" not in report_touched
    assert "ignored 1 pre-existing issues on untouched files" in report_touched

    # 2. When diff touches an unrelated file -> reported issues are 0 (passed)
    diff_unrelated = """diff --git a/other/file.py b/other/file.py
+++ b/other/file.py
"""
    report_unrelated = get_sonar_report(tmp_path, diff_unrelated)
    assert "[PASSED]" in report_unrelated
    assert "2 pre-existing baseline issues on untouched files ignored" in report_unrelated

def test_vector_normalization_and_fast_dot():
    """Tests L2 vector normalization and fast dot product similarity."""
    from context_harness import normalize_vector, fast_dot_product
    v1 = [3.0, 4.0]
    norm_v1 = normalize_vector(v1)
    assert pytest.approx(norm_v1[0], 0.001) == 0.6
    assert pytest.approx(norm_v1[1], 0.001) == 0.8

    # Dot product of identical unit vectors must equal 1.0
    assert pytest.approx(fast_dot_product(norm_v1, norm_v1), 0.001) == 1.0

def test_llm_factory_pricing_and_provider():
    """Validates multi-provider factory resolving models and pricing."""
    from llm_factory import get_provider, get_pricing_info
    assert get_provider() in ["gemini", "openai", "anthropic", "ollama"]
    flash_pricing = get_pricing_info("flash")
    pro_pricing = get_pricing_info("pro")
    assert "name" in flash_pricing
    assert "in" in flash_pricing
    assert "out" in flash_pricing
    assert "name" in pro_pricing

def test_extract_patch():
    """Tests extracting markdown unified diff patch blocks."""
    from gatekeeper import extract_patch
    text_with_patch = """Here is the suggested fix:
```diff
--- a/main.py
+++ b/main.py
@@ -1 +1 @@
-old
+new
```
That should fix it."""
    extracted = extract_patch(text_with_patch)
    assert extracted.startswith("--- a/main.py")
    assert "+new" in extracted

    # When no patch block exists
    assert extract_patch("No patch provided.") == ""
