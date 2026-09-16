import os
import sys
import time
from pathlib import Path
import operator
from typing import TypedDict, Dict, Annotated
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()

# Sincroniza chaves de API caso fornecido via GOOGLE_API_KEY ou GEMINI_API_KEY
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = api_key

# Configuração de Modelos e Preços de Referência (por 1M tokens)
PRICING = {
    "flash": {"name": "gemini-2.5-flash", "in": 0.075, "out": 0.30},
    "pro": {"name": "gemini-2.5-pro", "in": 1.25, "out": 5.00}
}

# Inicialização com fallback de chave para permitir imports em testes e mocks
_init_key = api_key or "mock-key-for-init"
flash_llm = ChatGoogleGenerativeAI(model=PRICING["flash"]["name"], temperature=0.1, google_api_key=_init_key)
pro_llm = ChatGoogleGenerativeAI(model=PRICING["pro"]["name"], temperature=0.2, google_api_key=_init_key)

# Definição do Estado Compartilhado
class AgentMetric(TypedDict):
    model: str
    in_tokens: int
    out_tokens: int
    duration_s: float
    cost_usd: float

class ReviewState(TypedDict):
    pr_diff: str
    harness_rules: str
    test_logs: str
    test_analysis: str
    code_review: str
    final_verdict: str
    # O operador.or_ combina dicionários de nós paralelos sem colisão no LangGraph
    telemetry: Annotated[Dict[str, AgentMetric], operator.or_]

# Helper para Telemetria e Custo
def run_agent(llm, tier: str, messages: list):
    start = time.time()
    response = llm.invoke(messages)
    elapsed = round(time.time() - start, 2)
    
    usage = getattr(response, "response_metadata", {}).get("usage_metadata", {})
    in_tok = usage.get("prompt_token_count", 0)
    out_tok = usage.get("candidates_token_count", 0)
    
    cost = ((in_tok / 1_000_000) * PRICING[tier]["in"]) + \
           ((out_tok / 1_000_000) * PRICING[tier]["out"])
           
    metric: AgentMetric = {
        "model": PRICING[tier]["name"],
        "in_tokens": in_tok,
        "out_tokens": out_tok,
        "duration_s": elapsed,
        "cost_usd": cost
    }
    return response.content, metric

# Nós Especialistas
def test_diagnostics_node(state: ReviewState):
    """Analisa se houve falha nos testes unitários/integração."""
    logs = state.get("test_logs", "")
    if not logs or ("FAIL" not in logs and "ERROR" not in logs and "FAILED" not in logs):
        return {"test_analysis": "✅ Todos os testes passaram sem erros."}
        
    prompt = [
        SystemMessage(content="Você é especialista em testes. Analise o log de erro e o diff. Diga qual teste quebrou, a causa exata e a linha do diff responsável."),
        HumanMessage(content=f"Logs de Teste:\n{logs}\n\nDiff do PR:\n{state.get('pr_diff', '')}")
    ]
    content, metric = run_agent(flash_llm, "flash", prompt)
    return {"test_analysis": content, "telemetry": {"tests": metric}}

def code_review_node(state: ReviewState):
    """Cruza o diff com as regras do docs/guidelines.md."""
    prompt = [
        SystemMessage(content="Você é um Staff Engineer. Revise o diff estritamente contra as regras do repositório (Harness). Aponte violações com severidade: BLOCKER ou WARNING."),
        HumanMessage(content=f"=== DIRETRIZES DO PROJETO ===\n{state.get('harness_rules', '')}\n\n=== DIFF ===\n{state.get('pr_diff', '')}")
    ]
    content, metric = run_agent(flash_llm, "flash", prompt)
    return {"code_review": content, "telemetry": {"review": metric}}

def supervisor_node(state: ReviewState):
    """Consolida os achados e toma a decisão com Gemini Pro."""
    prompt = [
        SystemMessage(content="Você é o Tech Lead responsável pelo Quality Gate. Emita o veredito final: APROVADO, APROVADO COM RESSALVAS ou REPROVADO. Se houver falha de teste ou violação BLOCKER, reprove."),
        HumanMessage(content=f"--- Diagnóstico de Testes ---\n{state.get('test_analysis', '')}\n\n--- Revisão Técnica ---\n{state.get('code_review', '')}")
    ]
    content, metric = run_agent(pro_llm, "pro", prompt)
    return {"final_verdict": content, "telemetry": {"supervisor": metric}}

# Montagem do Grafo
def build_graph():
    """Constrói e compila o grafo LangGraph do Quality Gatekeeper."""
    workflow = StateGraph(ReviewState)
    workflow.add_node("test_diagnostics", test_diagnostics_node)
    workflow.add_node("code_review", code_review_node)
    workflow.add_node("supervisor", supervisor_node)

    workflow.add_edge(START, "test_diagnostics")
    workflow.add_edge(START, "code_review")
    workflow.add_edge("test_diagnostics", "supervisor")
    workflow.add_edge("code_review", "supervisor")
    workflow.add_edge("supervisor", END)

    return workflow.compile()

app = build_graph()

def generate_report(result: ReviewState) -> str:
    """Gera o relatório formatado em Markdown com parecer e telemetria LLMOps."""
    telemetry = result.get("telemetry", {})
    total_tokens = sum(m["in_tokens"] + m["out_tokens"] for m in telemetry.values())
    total_cost = sum(m["cost_usd"] for m in telemetry.values())
    total_time = sum(m["duration_s"] for m in telemetry.values())

    rows = "\n".join([
        f"| `{k}` | `{v['model']}` | {v['in_tokens'] + v['out_tokens']:,} | {v['duration_s']}s | `${v['cost_usd']:.5f}` |"
        for k, v in telemetry.items()
    ])

    return f"""## 🛡️ AI Quality Gatekeeper Report

### 📋 Veredito do Supervisor
{result.get('final_verdict', 'Sem veredito.')}

### 🧪 Status dos Testes
{result.get('test_analysis', 'Não executado.')}

<details>
<summary><b>🔍 Detalhes da Revisão de Código</b></summary>

{result.get('code_review', 'Sem apontamentos.')}
</details>

---
### 📊 Telemetria da Execução (LLMOps)
| Agente | Modelo | Tokens | Tempo | Custo Est. |
| :--- | :--- | :--- | :--- | :--- |
{rows}
| **TOTAL** | — | **{total_tokens:,}** | **{total_time:.2f}s** | **`${total_cost:.5f} USD`** |
"""

def main():
    diff = Path("diff.txt").read_text(encoding="utf-8") if Path("diff.txt").exists() else ""
    tests = Path("tests.log").read_text(encoding="utf-8") if Path("tests.log").exists() else ""
    rules = Path("docs/guidelines.md").read_text(encoding="utf-8") if Path("docs/guidelines.md").exists() else ""

    if not diff.strip():
        print("Diff vazio. Encerrando.")
        sys.exit(0)

    initial_state = {
        "pr_diff": diff,
        "harness_rules": rules,
        "test_logs": tests,
        "telemetry": {}
    }

    result = app.invoke(initial_state)
    report = generate_report(result)
    Path("report.md").write_text(report, encoding="utf-8")
    print(report)

    if "REPROVADO" in result.get("final_verdict", "").upper():
        sys.exit(1)

# Execução direta
if __name__ == "__main__":
    main()