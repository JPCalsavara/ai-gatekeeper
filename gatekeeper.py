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

from sonar_adapter import get_sonar_report
from context_harness import retrieve_relevant_guidelines

load_dotenv()

# Synchronize API keys between GOOGLE_API_KEY and GEMINI_API_KEY
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = api_key

# Reference Model Pricing (per 1M tokens)
PRICING = {
    "flash": {"name": "gemini-2.5-flash", "in": 0.075, "out": 0.30},
    "pro": {"name": "gemini-2.5-pro", "in": 1.25, "out": 5.00}
}

# Initialization with key fallback to allow imports during test execution and mocking
_init_key = api_key or "mock-key-for-init"
flash_llm = ChatGoogleGenerativeAI(model=PRICING["flash"]["name"], temperature=0.1, google_api_key=_init_key)
pro_llm = ChatGoogleGenerativeAI(model=PRICING["pro"]["name"], temperature=0.2, google_api_key=_init_key)

# Shared State Definition
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
    sonar_issues: str
    test_analysis: str
    code_review: str
    sonar_analysis: str
    final_verdict: str
    # operator.or_ merges dictionaries from parallel branches without state collisions in LangGraph
    telemetry: Annotated[Dict[str, AgentMetric], operator.or_]

# Helper for Telemetry and Cost Calculation
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

# Specialist Nodes
def test_diagnostics_node(state: ReviewState):
    """Analyzes test logs for unit or integration failures against git diff."""
    logs = state.get("test_logs", "")
    if not logs or ("FAIL" not in logs and "ERROR" not in logs and "FAILED" not in logs):
        return {"test_analysis": "[PASSED] All tests passed with no errors."}
        
    prompt = [
        SystemMessage(content="You are a test triage specialist. Analyze the test error logs and the PR diff. Identify which test broke, the root cause, and the exact responsible lines in the diff. Provide a fix patch suggestion."),
        HumanMessage(content=f"Test Logs:\n{logs}\n\nPR Diff:\n{state.get('pr_diff', '')}")
    ]
    content, metric = run_agent(flash_llm, "flash", prompt)
    return {"test_analysis": content, "telemetry": {"tests": metric}}

def code_review_node(state: ReviewState):
    """Reviews the PR diff strictly against guidelines (Context Harness)."""
    rules = state.get("harness_rules", "")
    diff = state.get("pr_diff", "")

    # If context_harness.json exists, semantically retrieve the most relevant guidelines
    if Path("context_harness.json").exists():
        semantic_rules = retrieve_relevant_guidelines(diff, Path("context_harness.json"), top_k=4)
        if semantic_rules.strip():
            rules = semantic_rules

    prompt = [
        SystemMessage(content="You are a Staff Engineer. Review the PR diff strictly against repository guidelines (Context Harness). Flag violations categorized as BLOCKER or WARNING with clear remediation guidance."),
        HumanMessage(content=f"=== PROJECT GUIDELINES ===\n{rules}\n\n=== PR DIFF ===\n{diff}")
    ]
    content, metric = run_agent(flash_llm, "flash", prompt)
    return {"code_review": content, "telemetry": {"review": metric}}

def sonar_triage_node(state: ReviewState):
    """Triages SonarQube static analysis issues and correlates them with the diff."""
    issues = state.get("sonar_issues", "")
    if not issues:
        return {"sonar_analysis": "[PASSED] No SonarQube issues detected."}

    prompt = [
        SystemMessage(content="You are a static analysis remediation engineer. Review the reported SonarQube issues and cross-reference them with the PR diff. Highlight blocker vulnerabilities or critical code smells and provide exact code patch remediation."),
        HumanMessage(content=f"SonarQube Issues:\n{issues}\n\nPR Diff:\n{state.get('pr_diff', '')}")
    ]
    content, metric = run_agent(flash_llm, "flash", prompt)
    return {"sonar_analysis": content, "telemetry": {"sonar": metric}}

def supervisor_node(state: ReviewState):
    """Consolidates findings and issues the final gatekeeper decision with Gemini Pro."""
    prompt = [
        SystemMessage(content="You are the Tech Lead responsible for the Quality Gate. Provide the final verdict: APPROVED, APPROVED WITH WARNINGS, or REJECTED. If there is a test failure, SonarQube BLOCKER, or guideline BLOCKER violation, you MUST mark it as REJECTED."),
        HumanMessage(content=f"--- Test Diagnostics ---\n{state.get('test_analysis', '')}\n\n--- Technical Review ---\n{state.get('code_review', '')}\n\n--- SonarQube Analysis ---\n{state.get('sonar_analysis', '')}")
    ]
    content, metric = run_agent(pro_llm, "pro", prompt)
    return {"final_verdict": content, "telemetry": {"supervisor": metric}}

# Graph Construction
def build_graph():
    """Builds and compiles the LangGraph state machine for the Quality Gatekeeper."""
    workflow = StateGraph(ReviewState)
    workflow.add_node("test_diagnostics", test_diagnostics_node)
    workflow.add_node("code_review", code_review_node)
    workflow.add_node("sonar_triage", sonar_triage_node)
    workflow.add_node("supervisor", supervisor_node)

    workflow.add_edge(START, "test_diagnostics")
    workflow.add_edge(START, "code_review")
    workflow.add_edge(START, "sonar_triage")

    workflow.add_edge("test_diagnostics", "supervisor")
    workflow.add_edge("code_review", "supervisor")
    workflow.add_edge("sonar_triage", "supervisor")

    workflow.add_edge("supervisor", END)

    return workflow.compile()

app = build_graph()

def generate_report(result: ReviewState) -> str:
    """Generates the Markdown report with decision and LLMOps telemetry."""
    telemetry = result.get("telemetry", {})
    total_tokens = sum(m["in_tokens"] + m["out_tokens"] for m in telemetry.values())
    total_cost = sum(m["cost_usd"] for m in telemetry.values())
    total_time = sum(m["duration_s"] for m in telemetry.values())

    rows = "\n".join([
        f"| `{k}` | `{v['model']}` | {v['in_tokens'] + v['out_tokens']:,} | {v['duration_s']}s | `${v['cost_usd']:.5f}` |"
        for k, v in telemetry.items()
    ])

    sonar_section = ""
    sonar_analysis = result.get("sonar_analysis", "")
    if sonar_analysis and "[PASSED]" not in sonar_analysis:
        sonar_section = f"""
### SonarQube Triage Findings
{sonar_analysis}
"""

    return f"""## AI Quality Gatekeeper Report

### Supervisor Verdict
{result.get('final_verdict', 'No verdict provided.')}

### Test Execution Status
{result.get('test_analysis', 'Not executed.')}
{sonar_section}
<details>
<summary><b>Code Review Findings</b></summary>

{result.get('code_review', 'No issues detected.')}
</details>

---
### Execution Telemetry (LLMOps)
| Agent | Model | Tokens | Time | Est. Cost |
| :--- | :--- | :--- | :--- | :--- |
{rows}
| **TOTAL** | — | **{total_tokens:,}** | **{total_time:.2f}s** | **`${total_cost:.5f} USD`** |
"""

def main():
    diff = Path("diff.txt").read_text(encoding="utf-8") if Path("diff.txt").exists() else ""
    tests = Path("tests.log").read_text(encoding="utf-8") if Path("tests.log").exists() else ""
    rules = Path("docs/guidelines.md").read_text(encoding="utf-8") if Path("docs/guidelines.md").exists() else ""
    sonar_report = get_sonar_report(Path("."))

    if not diff.strip():
        print("Diff is empty. Exiting.")
        sys.exit(0)

    initial_state = {
        "pr_diff": diff,
        "harness_rules": rules,
        "test_logs": tests,
        "sonar_issues": sonar_report,
        "telemetry": {}
    }

    result = app.invoke(initial_state)
    report = generate_report(result)
    Path("report.md").write_text(report, encoding="utf-8")
    print(report)

    verdict = result.get("final_verdict", "").upper()
    if "REJECTED" in verdict or "REPROVADO" in verdict:
        sys.exit(1)

# Direct execution
if __name__ == "__main__":
    main()