# Lean Canvas & MVP Definition: Autonomous AI Quality Gatekeeper

> **Lean Approach:** Instead of building the entire ecosystem at once (Jira + Slack + Sonar + ChromaDB + complex multi-agent setups), we map the lean business model and scope down to the **Minimum Viable Product (MVP)** to validate market demand with minimal effort and maximum impact.

---

## 1. Project Lean Canvas

### Visual Business Model Diagram

```mermaid
flowchart TD
    subgraph LeanCanvas["Lean Canvas: Autonomous AI Quality Gatekeeper"]
        direction TB

        subgraph CanvasTop["Core Value Structure & Market"]
            direction LR

            subgraph B1["1. PROBLEM"]
                direction TB
                P1["- Alert fatigue and false positives in traditional linters"]
                P2["- Disconnect between internal architectural rules and PR code"]
                P3["- High costs and privacy concerns with closed SaaS solutions"]
            end

            subgraph B4["4. SOLUTION"]
                direction TB
                S1["- Intelligent triage of test failures (correlates logs with diff)"]
                S2["- Reconciliation with repository rules (Context Harness)"]
                S3["- Transparent token and cost telemetry (USD) on the PR"]
            end

            subgraph B3["3. VALUE PROPOSITION"]
                direction TB
                PV["'The open, BYOK AI Quality Gate that reconciles broken tests and internal guidelines directly inside your CI/CD, for fractions of a cent per PR.'"]
            end

            subgraph B9["9. UNFAIR ADVANTAGE"]
                direction TB
                VI1["- Agnostic BYOK architecture executing inside the company runner with full privacy and zero lock-in"]
                VI2["- Dynamic Model Tiering (Flash + Pro) reducing costs by over 85% compared to proprietary SaaS"]
            end

            subgraph B2["2. CUSTOMER SEGMENTS"]
                direction TB
                SC1["- Early Adopters: Tech Leads and Senior Devs tired of wasting time on broken PRs and CI noise"]
                SC2["- Engineering teams in regulated industries (Fintech, Healthtech) unable to use external SaaS"]
            end
        end

        subgraph CanvasBottom["Distribution, Metrics and Monetization"]
            direction LR

            subgraph B7["7. KEY METRICS"]
                direction TB
                M1["- Analyzed PRs / month"]
                M2["- Acceptance rate of suggested patches"]
                M3["- GitHub Stars and Forks"]
                M4["- Average cost per PR maintained below $0.005 USD"]
            end

            subgraph B8["8. CHANNELS"]
                direction TB
                C1["- GitHub Marketplace (Official Action)"]
                C2["- Technical communities (Reddit, Hacker News, LinkedIn)"]
                C3["- Technical engineering content (architecture breakdowns, tutorials)"]
            end

            subgraph B5["5. REVENUE STREAMS"]
                direction TB
                R1["- Phase 1 (Open-Source): Sponsorships (GitHub Sponsors) and portfolio authority"]
                R2["- Phase 2 (Open-Core): Enterprise web dashboard for centralized team metrics"]
            end
        end
    end
```

### Detailed Lean Canvas Blocks

| Block | Details |
| :--- | :--- |
| **1. Problem** | - Alert fatigue and false positives in traditional linters.<br/>- Disconnect between internal architectural guidelines (RFCs) and submitted PR code.<br/>- Prohibitive costs and privacy concerns with proprietary AI SaaS solutions. |
| **4. Solution** | - Intelligent triage of test failures (correlating CI logs directly with diff).<br/>- Automated reconciliation with repository guidelines (Context Harness).<br/>- Transparent token and cost telemetry (USD) visible in the PR comment. |
| **3. Unique Value Proposition** | *"The open, BYOK AI Quality Gate that reconciles broken tests and internal guidelines directly inside your CI/CD, for fractions of a cent per PR."* |
| **9. Unfair Advantage** | - **Agnostic Architecture (BYOK):** Runs entirely within the organization's runner, ensuring complete privacy with zero vendor lock-in.<br/>- **Dynamic Model Tiering (Flash + Pro):** Cuts LLM costs by over 85% compared to monolithic models. |
| **2. Customer Segments** | - **Early Adopters:** Tech Leads and Senior Engineers fatigued by manual CI log inspection and noisy PRs.<br/>- **Engineering Teams:** Organizations with compliance and privacy constraints (Fintechs, Healthtechs) prohibited from sending code to external SaaS vendors. |
| **8. Channels** | - GitHub Marketplace (Official Action).<br/>- Technical developer communities (Reddit `r/devops`, Hacker News, LinkedIn).<br/>- Engineering content (deep-dive architecture articles and practical tutorials). |
| **7. Key Metrics** | - Analyzed PRs per month.<br/>- Acceptance rate of suggested code patches.<br/>- GitHub repository Stars and Forks.<br/>- Average cost per PR maintained below $0.005 USD. |
| **5. Revenue Streams** | - **Phase 1 (Open-Source):** Sponsorships (GitHub Sponsors) and portfolio authority.<br/>- **Phase 2 (Open-Core):** Enterprise web dashboard for aggregated cross-team metrics and governance. |

---

## 2. Initial Scope Pitfall: The Risk of Overengineering

Attempting to implement all features simultaneously:
- [ ] Jira MCP Server
- [ ] Slack MCP Server
- [ ] Local vector ChromaDB
- [ ] Deep SonarQube SARIF integration
- [ ] 5-agent cyclical graph...

Result: The project would take months to deliver, would be difficult to debug, and early adoption would stall.

> **Lean Principle:** Identify the thinnest vertical slice that delivers immediate value on first execution.

---

## 3. Lean Scope: Phase Decomposition

```mermaid
flowchart TD
    V01["MVP v0.1 (Week 1) - Core Value\n- Broken Test Diagnostics (Logs + Diff)\n- 1 Static Guidelines File (docs/guidelines.md)\n- 2 LangGraph Nodes: Flash (Analysis) + Pro (Decision)\n- Cost telemetry posted in PR comment"]

    V02["Version v0.2 (Weeks 2-3) - Context Harness & Sonar\n- Local RAG with ChromaDB for repositories with RFCs\n- Deterministic Sonar report ingestion\n- Packaging as an official GitHub Action"]

    V10["Version v1.0 (Future) - Enterprise MCP Connectors\n- MCP Integration with Jira (Acceptance Criteria)\n- MCP Integration with Slack (Channel decisions)\n- Multi-repository governance dashboard"]

    V01 -->|"User validation"| V02
    V02 -->|"Community traction"| V10

    classDef mvp fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef v02 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1.5px;
    classDef v10 fill:#fff3e0,stroke:#f57c00,stroke-width:1.5px;
    class V01 mvp;
    class V02 v02;
    class V10 v10;
```

---

## 4. MVP v0.1 Specification (Current Scope)

### Problem Solved on Day 1
Developers dislike opening a PR, seeing a failing CI pipeline, and scrolling through 500 lines of raw GitHub Actions logs to pinpoint the issue.

### MVP v0.1 Components

1. **Input 1:** The `diff.txt` generated by git.
2. **Input 2:** The `tests.log` extracted from test runners (PyTest, Jest, Go test, etc.).
3. **Input 3:** A `docs/guidelines.md` file (basic architectural rules injected directly into the prompt without a vector database).
4. **Lean LangGraph Orchestration (2 Nodes):**
   - **Node 1 (Gemini 2.5 Flash):** Analyzes test logs, correlates with modified lines in diff, and identifies the root cause.
   - **Node 2 (Gemini 2.5 Pro):** Validates severity, checks adherence to `guidelines.md`, and formats the final verdict.
5. **Output:** A GitHub PR comment containing:
   - Specific failed test and responsible diff line;
   - Remediation code patch suggestion;
   - LLMOps telemetry table displaying exact cost in cents (USD).

### Pipeline Architecture

```mermaid
flowchart TD
    subgraph Inputs["1. Inputs (CI Runner)"]
        direction TB
        E1["diff.txt\n(Git Diff of changes)"]
        E2["tests.log\n(Test runner execution output)"]
        E3["docs/guidelines.md\n(Repository guidelines)"]
    end

    subgraph LangGraph["2. LangGraph Orchestration (2 Nodes)"]
        direction TB
        N1["Node 1: Gemini 2.5 Flash\n- Failure triage\n- Correlate logs with diff\n- Root cause identification"]
        N2["Node 2: Gemini 2.5 Pro\n- Severity validation\n- Guidelines compliance\n- Final patch generation"]
        N1 -->|"Preliminary diagnostics"| N2
    end

    subgraph Output["3. Output (GitHub PR Comment)"]
        direction TB
        O1["Identification of broken test and responsible diff line"]
        O2["Suggested remediation code patch"]
        O3["LLMOps telemetry and cost table (< $0.003 USD)"]
    end

    E1 --> N1
    E2 --> N1
    E3 --> N2
    N2 --> Output

    classDef inputStyle fill:#f0f4c3,stroke:#9e9d24,stroke-width:1.5px;
    classDef nodeStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px;
    classDef outputStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    class E1,E2,E3 inputStyle;
    class N1,N2 nodeStyle;
    class O1,O2,O3 outputStyle;
```

---

## 5. 7-Day Lean Validation Experiment

To validate real adoption before committing weeks to complex third-party connectors:

```mermaid
flowchart LR
    D1["Days 1-2:\nBuild MVP\n(gatekeeper.py + CI)"]
    D2["Day 3:\nPublic repo,\nclean README & GIF/print"]
    D3["Day 4:\nBYOK trial with\npeer AI engineer"]
    D4["Days 5-6:\nTechnical article\n(LinkedIn / Dev.to)"]
    D5["Day 7:\nMeasure interest\nand validate demand"]

    D1 --> D2 --> D3 --> D4 --> D5

    classDef stepStyle fill:#fce4ec,stroke:#c2185b,stroke-width:1.5px;
    class D1,D2,D3,D4,D5 stepStyle;
```

### Daily Action Plan

1. **Days 1 and 2:** Implement the Python script (`gatekeeper.py`) using LangGraph and standard GitHub Actions workflow.
2. **Day 3:** Set up a public repository with documentation, showing a real PR review with test diagnostics and cost telemetry.
3. **Day 4:** Test with a peer engineer:
   - Provide instructions to run with their own `GEMINI_API_KEY`.
   - Collect immediate feedback: Was onboarding fast? Was the feedback actionable?
4. **Days 5 and 6:** Publish a concise technical post:
   > *"Why we stopped paying $40/dev for proprietary PR review tools and built an open Quality Gatekeeper with Gemini Flash for $0.002 per run."*
5. **Day 7:** Measure demand:
   - Inquiries regarding Sonar, Jira, or custom linters validate feature expansion before writing complex code.

---

## 6. Success Metrics (Go / No-Go)

| Validation Metric | Minimum Target (Success) |
| :--- | :--- |
| **Onboarding Time** | A new engineer can run the tool in their repository in **under 5 minutes**. |
| **Diagnostic Accuracy** | Correctly identifies the line causing test failure in **at least 8 out of 10 real cases**. |
| **Cost per PR** | Average execution cost maintained **below $0.003 USD**. |
| **False Positives** | **Zero recommendations** that contradict rules defined in `docs/guidelines.md`. |
