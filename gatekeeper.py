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
from llm_factory import get_chat_model, get_pricing_info

load_dotenv()

# Reference Model Pricing (per 1M tokens) resolved via factory
PRICING = {
    "flash": get_pricing_info("flash"),
    "pro": get_pricing_info("pro")
}

# Initialization via factory supporting Gemini, OpenAI, Anthropic, Ollama
flash_llm = get_chat_model("flash", temperature=0.1)
pro_llm = get_chat_model("pro", temperature=0.2)

IGNORE_PATTERNS = [
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Cargo.lock",
    "composer.lock",
    ".min.js",
    ".min.css",
    "dist/",
    "build/",
    ".map",
]

def clean_diff(raw_diff: str, max_chars: int = 40000) -> str:
    """
    Cleans raw git diff:
    1. Filters out high-noise lockfiles, build artifacts, and minified bundles.
    2. Enforces max_chars limit with graceful truncation warning to prevent token saturation.
    """
    if not raw_diff:
        return ""

    file_chunks = []
    current_chunk = []
    current_file = ""

    for line in raw_diff.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if current_chunk:
                file_chunks.append((current_file, "".join(current_chunk)))
                current_chunk = []
            parts = line.split()
            current_file = parts[2][2:] if len(parts) >= 3 and parts[2].startswith("a/") else ""
        current_chunk.append(line)

    if current_chunk:
        file_chunks.append((current_file, "".join(current_chunk)))

    kept_chunks = []
    filtered_count = 0
    for filename, chunk in file_chunks:
        if any(pattern in filename for pattern in IGNORE_PATTERNS):
            filtered_count += 1
            kept_chunks.append(f"# [IGNORED NOISY FILE: {filename}]\n")
        else:
            kept_chunks.append(chunk)

    result = "".join(kept_chunks)
    if len(result) > max_chars:
        result = result[:max_chars] + f"\n\n# [DIFF TRUNCATED: Exceeded {max_chars} characters budget to prevent token saturation]\n"

    return result

def extract_patch(text: str) -> str:
    """Extracts a git diff/patch block from text if present."""
    import re
    match = re.search(r"```(?:diff|patch)\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def apply_patch_if_requested(verdict_text: str, target_dir: Path) -> bool:
    """Attempts to apply suggested patch to target directory using git apply."""
    patch_content = extract_patch(verdict_text)
    if not patch_content:
        print("[INFO] No unified patch block found in supervisor verdict.")
        return False

    patch_file = target_dir / "gatekeeper_suggestion.patch"
    patch_file.write_text(patch_content + "\n", encoding="utf-8")
    print(f"[INFO] Patch written to {patch_file}")

    import subprocess
    res = subprocess.run(
        ["git", "-C", str(target_dir), "apply", "--check", str(patch_file)],
        capture_output=True,
        text=True
    )
    if res.returncode == 0:
        subprocess.run(["git", "-C", str(target_dir), "apply", str(patch_file)], check=True)
        print("[SUCCESS] Successfully applied supervisor suggested patch to workspace.")
        return True
    else:
        print(f"[WARN] Patch could not be automatically applied cleanly: {res.stderr.strip()}")
        return False

# Shared State Definition
class AgentMetric(TypedDict):
    model: str
    in_tokens: int
    out_tokens: int
    duration_s: float
    cost_usd: float

class ReviewState(TypedDict, total=False):
    pr_diff: str
    harness_rules: str
    harness_file: str
    test_logs: str
    sonar_issues: str
    test_analysis: str
    code_review: str
    sonar_analysis: str
    final_verdict: str
    # operator.or_ merges dictionaries from parallel branches without state collisions in LangGraph
    telemetry: Annotated[Dict[str, AgentMetric], operator.or_]

def extract_text(content) -> str:
    """Safely extracts plain text from LangChain message content (str or list of dicts)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return "\n".join(parts)
    return str(content)

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
    return extract_text(response.content), metric

# Specialist Nodes
def test_diagnostics_node(state: ReviewState):
    """Analyzes test logs for unit or integration failures against git diff."""
    logs = state.get("test_logs", "")
    if not logs or ("FAIL" not in logs and "ERROR" not in logs and "FAILED" not in logs):
        return {"test_analysis": "[PASSED] All tests passed with no errors."}
        
    prompt = [
        SystemMessage(content="You are a test triage specialist. Analyze the test error logs and the PR diff. Identify which test broke, the root cause, and the exact responsible lines in the diff. Provide a fix patch suggestion. Do not use emojis in your response."),
        HumanMessage(content=f"Test Logs:\n{logs}\n\nPR Diff:\n{state.get('pr_diff', '')}")
    ]
    content, metric = run_agent(flash_llm, "flash", prompt)
    return {"test_analysis": content, "telemetry": {"tests": metric}}

def code_review_node(state: ReviewState):
    """Reviews the PR diff strictly against guidelines (Context Harness)."""
    rules = state.get("harness_rules", "")
    diff = state.get("pr_diff", "")
    harness_path = Path(state.get("harness_file", "context_harness.json"))

    # If harness index exists, semantically retrieve the most relevant guidelines
    if harness_path.exists():
        semantic_rules = retrieve_relevant_guidelines(diff, harness_path, top_k=4)
        if semantic_rules.strip():
            rules = semantic_rules

    prompt = [
        SystemMessage(content="You are a Staff Engineer. Review the PR diff strictly against repository guidelines (Context Harness). Flag violations categorized as BLOCKER or WARNING with clear remediation guidance. Do not use emojis in your response."),
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
        SystemMessage(content="You are a static analysis remediation engineer. Review the reported SonarQube issues and cross-reference them with the PR diff. Highlight blocker vulnerabilities or critical code smells and provide exact code patch remediation. Do not use emojis in your response."),
        HumanMessage(content=f"SonarQube Issues:\n{issues}\n\nPR Diff:\n{state.get('pr_diff', '')}")
    ]
    content, metric = run_agent(flash_llm, "flash", prompt)
    return {"sonar_analysis": content, "telemetry": {"sonar": metric}}

def supervisor_node(state: ReviewState):
    """Consolidates findings and issues the final gatekeeper decision with Gemini Pro (fallback to Flash if needed)."""
    prompt = [
        SystemMessage(content="You are the Tech Lead responsible for the Quality Gate. Provide the final verdict: APPROVED, APPROVED WITH WARNINGS, or REJECTED. If there is a test failure, SonarQube BLOCKER, or guideline BLOCKER violation, you MUST mark it as REJECTED. Do not use emojis in your response."),
        HumanMessage(content=f"--- Test Diagnostics ---\n{state.get('test_analysis', '')}\n\n--- Technical Review ---\n{state.get('code_review', '')}\n\n--- SonarQube Analysis ---\n{state.get('sonar_analysis', '')}")
    ]
    try:
        content, metric = run_agent(pro_llm, "pro", prompt)
    except Exception as e:
        print(f"[WARN] Pro model invocation failed ({e}). Falling back to Flash model for Supervisor.")
        content, metric = run_agent(flash_llm, "flash", prompt)
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
    import argparse
    parser = argparse.ArgumentParser(description="AI Quality Gatekeeper")
    parser.add_argument("--target", type=str, default=".", help="Target project root directory")
    parser.add_argument("--diff", type=str, default=None, help="Path to diff file")
    parser.add_argument("--tests", type=str, default=None, help="Path to tests.log file")
    parser.add_argument("--guidelines", type=str, default=None, help="Path to guidelines.md")
    parser.add_argument("--harness", type=str, default=None, help="Path to context_harness.json")
    parser.add_argument("--output", type=str, default=None, help="Path to report.md output")
    parser.add_argument("--apply-patch", action="store_true", help="Automatically apply remediation patch to workspace if available")

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    diff_path = Path(args.diff) if args.diff else target_path / "diff.txt"
    tests_path = Path(args.tests) if args.tests else target_path / "tests.log"
    guidelines_path = Path(args.guidelines) if args.guidelines else target_path / "docs" / "guidelines.md"
    harness_path = Path(args.harness) if args.harness else target_path / "context_harness.json"
    report_path = Path(args.output) if args.output else target_path / "report.md"

    raw_diff = diff_path.read_text(encoding="utf-8") if diff_path.exists() else ""
    diff = clean_diff(raw_diff)
    tests = tests_path.read_text(encoding="utf-8") if tests_path.exists() else ""
    rules = guidelines_path.read_text(encoding="utf-8") if guidelines_path.exists() else ""
    sonar_report = get_sonar_report(target_path, diff)

    if not diff.strip():
        print(f"Diff is empty ({diff_path}). Exiting.")
        sys.exit(0)

    initial_state = {
        "pr_diff": diff,
        "harness_rules": rules,
        "harness_file": str(harness_path),
        "test_logs": tests,
        "sonar_issues": sonar_report,
        "telemetry": {}
    }

    result = app.invoke(initial_state)
    report = generate_report(result)
    report_path.write_text(report, encoding="utf-8")
    print(report)

    if args.apply_patch:
        apply_patch_if_requested(result.get("final_verdict", ""), target_path)

    verdict = result.get("final_verdict", "").upper()
    if "REJECTED" in verdict or "REPROVADO" in verdict:
        sys.exit(1)

# Direct execution
if __name__ == "__main__":
    main()