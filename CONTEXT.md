# AI Quality Gatekeeper Domain Context

Autonomous Pull Request Quality Gatekeeper built with LangGraph and Dynamic Model Tiering for automated test triage, architectural guideline enforcement, SonarQube static analysis remediation, and LLMOps cost accounting.

## Ubiquitous Language & Glossary

**Quality Gate**:
The definitive CI/CD evaluation step that inspects pull request changes and renders a binary or conditional status (`APPROVED`, `APPROVED WITH WARNINGS`, or `REJECTED`).
_Avoid_: Build check, linter pass, code review script, pipeline gate

**LangGraph Orchestrator**:
The stateful, cyclic or DAG multi-agent graph engine (`gatekeeper.py`) coordinating parallel evaluation nodes (`test_diagnostics`, `code_review`, `sonar_triage`) and a synthesis node (`supervisor`).
_Avoid_: Pipeline chain, sequential prompt script, agent workflow runner

**Dynamic Model Tiering**:
The architectural pattern that routes high-volume parallel triage tasks to economical, low-latency models (Flash Tier) while reserving high-reasoning models (Pro Tier) exclusively for supervisor synthesis.
_Avoid_: Model switching, prompt routing, cascade calling

**Flash Tier**:
High-throughput, sub-second latency model execution (e.g., `gemini-3.5-flash-lite`, `gpt-4o-mini`, `claude-3-5-haiku`, `llama3.2`) tasked with parsing large diffs, test logs, and static analysis outputs.
_Avoid_: Small model, cheap LLM, worker node

**Pro Tier**:
High-reasoning model execution (e.g., `gemini-3.5-flash-lite` in standard mode, `gemini-3.1-pro-preview`, `gpt-4o`, `claude-3-5-sonnet`, `qwen2.5-coder`) tasked with resolving conflicting evidence and generating synthesized remediation diffs.
_Avoid_: Big model, smart LLM, master node

**Context Harness**:
The local semantic retrieval system (`context_harness.py` and `context_harness.json`) that pre-normalizes embedding vectors and extracts relevant repository guidelines using accelerated dot product similarity.
_Avoid_: Vector database, RAG pipeline, knowledge base, memory store

**SonarQube Adapter**:
The unified static analysis ingestion module (`sonar_adapter.py`) that queries SonarCloud/SonarQube REST APIs or parses SARIF/JSON files with diff-aware filtering.
_Avoid_: Sonar plugin, static code checker, issue fetcher

**Diff Preprocessing (`clean_diff`)**:
The sanitization layer that strips noisy lockfiles, vendor dependencies, and minified assets before passing the pull request diff to LLM prompts.
_Avoid_: Diff trimming, git filter, text shortening

**Automated Remediation Patch (`--apply-patch`)**:
A validated unified diff block synthesized by the supervisor that can be verified (`git apply --check`) and safely applied to the workspace.
_Avoid_: Auto-fix, code generator, quick-fix

**Baseline Technical Debt**:
Pre-existing SonarQube or linting issues on untouched files present in the base branch. In v1.0.0+, these are filtered out and counted as ignored to prevent false gate rejections.
_Avoid_: Legacy bugs, unassigned issues, background errors

**LLMOps Cost Telemetry**:
The structured metrics table generated in every review report detailing exact token consumption, execution latency in seconds, and estimated USD cost.
_Avoid_: Token stats, timing info, usage logs
