# ADR 0001: LangGraph for Quality Gate Orchestration

## Status
Accepted

## Context
The AI Quality Gatekeeper needs to run multiple independent evaluation passes over a Pull Request:
1. Test failure traceback correlation with git diff.
2. Architecture guidelines compliance via Context Harness semantic search.
3. SonarQube static analysis triage with diff-aware filtering.
4. Supervisor synthesis to render an authoritative verdict (`APPROVED` or `REJECTED`) and generate remediation patches.

Running these evaluations sequentially produces cumulative latency (8s to 20s). Moreover, linear prompt chaining lacks state management and structured error isolation.

## Decision
We adopted **LangGraph** (`StateGraph`) with a fan-out / fan-in topology:
- Three parallel worker nodes (`test_diagnostics`, `code_review`, `sonar_triage`) execute concurrently.
- Each worker node updates its respective state slice in `ReviewState` and records granular LLMOps telemetry.
- A single `supervisor` node consolidates the state and renders the final verdict.

## Consequences
- **Positive**:
  - Predictable execution DAG with typed state definitions (`ReviewState`).
  - Total latency equals `max(parallel_nodes) + supervisor`, typically under 3.5s.
  - LLMOps telemetry easily collected from all nodes.
- **Negative**:
  - Adds dependency on `langgraph` core package.
