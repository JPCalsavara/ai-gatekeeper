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

# Alias para evitar que o pytest trate a função do gatekeeper como caso de teste
diagnose_tests_node = gatekeeper.test_diagnostics_node

def test_pricing_keys_exist():
    """Valida se as chaves e modelos de precificação estão definidos."""
    assert "flash" in PRICING
    assert "pro" in PRICING
    assert PRICING["flash"]["name"] == "gemini-2.5-flash"
    assert PRICING["pro"]["name"] == "gemini-2.5-pro"

def test_run_agent_telemetry_calculation(mock_flash_response):
    """Testa se run_agent calcula tokens, duração e custo corretamente."""
    mock_llm = MagicMock()
    mock_resp = mock_flash_response("Análise de teste concluída", in_tokens=1_000_000, out_tokens=1_000_000)
    mock_llm.invoke.return_value = mock_resp

    content, metric = run_agent(mock_llm, "flash", [])

    assert content == "Análise de teste concluída"
    assert metric["model"] == "gemini-2.5-flash"
    assert metric["in_tokens"] == 1_000_000
    assert metric["out_tokens"] == 1_000_000
    # in: 0.075, out: 0.30 -> total = 0.375
    assert pytest.approx(metric["cost_usd"], 0.0001) == 0.375
    assert metric["duration_s"] >= 0.0

def test_test_diagnostics_node_when_tests_pass():
    """Se os testes passaram, não deve chamar o LLM nem gerar custo desnecessário."""
    state: ReviewState = {
        "pr_diff": "diff content",
        "harness_rules": "rules content",
        "test_logs": "4 passed in 0.42s",
        "telemetry": {}
    }

    result = diagnose_tests_node(state)

    assert "✅ Todos os testes passaram sem erros." in result["test_analysis"]
    assert "telemetry" not in result

def test_test_diagnostics_node_when_tests_fail():
    """Se os testes falharam, deve acionar o nó de diagnóstico e registrar telemetria."""
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

    with patch("gatekeeper.run_agent", return_value=("Falha na linha 15.", mock_metric)) as mock_run:
        result = diagnose_tests_node(state)
        assert mock_run.called
        assert "Falha na linha 15." in result["test_analysis"]
        assert "tests" in result["telemetry"]
        assert result["telemetry"]["tests"]["model"] == "gemini-2.5-flash"

def test_code_review_node():
    """Testa a execução do nó de revisão de código."""
    state: ReviewState = {
        "pr_diff": "query = f'SELECT * FROM users WHERE id = {user_id}'",
        "harness_rules": "Nunca use concatenação de string em SQL (BLOCKER)",
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

    with patch("gatekeeper.run_agent", return_value=("BLOCKER: SQL Injection detectado.", mock_metric)):
        result = code_review_node(state)

    assert "BLOCKER" in result["code_review"]
    assert "review" in result["telemetry"]

def test_supervisor_node():
    """Testa o nó supervisor emitindo o veredito final com Gemini Pro."""
    state: ReviewState = {
        "pr_diff": "diff",
        "harness_rules": "rules",
        "test_logs": "logs",
        "test_analysis": "Testes passaram",
        "code_review": "BLOCKER detectado",
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

    with patch("gatekeeper.run_agent", return_value=("REPROVADO: Violação crítica.", mock_metric)):
        result = supervisor_node(state)

    assert "REPROVADO" in result["final_verdict"]
    assert "supervisor" in result["telemetry"]

def test_full_graph_execution():
    """Executa o grafo compilado fim-a-fim garantindo concorrência e junção de telemetria."""
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
            return "Diagnóstico ou revisão Flash", metric
        return "VEREDITO: REPROVADO", metric

    with patch("gatekeeper.run_agent", side_effect=mock_run_agent_side_effect):
        result = app.invoke(initial_state)

    assert result["final_verdict"] == "VEREDITO: REPROVADO"
    assert "tests" in result["telemetry"]
    assert "review" in result["telemetry"]
    assert "supervisor" in result["telemetry"]

def test_generate_report_formatting():
    """Valida a geração do relatório Markdown e cálculo de totais."""
    sample_result: ReviewState = {
        "pr_diff": "diff",
        "harness_rules": "rules",
        "test_logs": "logs",
        "test_analysis": "✅ Todos os testes passaram sem erros.",
        "code_review": "Nenhuma inconformidade encontrada.",
        "final_verdict": "APROVADO",
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

    assert "## 🛡️ AI Quality Gatekeeper Report" in report
    assert "APROVADO" in report
    assert "gemini-2.5-flash" in report
    assert "gemini-2.5-pro" in report
    assert "TOTAL" in report
    assert "$0.00232 USD" in report or "0.00232" in report
