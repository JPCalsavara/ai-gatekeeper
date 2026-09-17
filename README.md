# AI Quality Gatekeeper

> Autonomous PR Quality Gatekeeper built with **LangGraph** and **Dynamic Model Tiering** (Gemini 2.5 Flash + Pro). Automated test failure triage, architecture guideline enforcement (Context Harness with local JSON embeddings), SonarQube/SonarCloud static analysis triage, and open LLMOps cost telemetry directly in your CI/CD.

---

## Overview and Architecture

AI Quality Gatekeeper integrates into continuous integration pipelines to resolve three major friction points in modern engineering teams:
1. **CI Log Fatigue:** Eliminates time spent manually parsing hundreds of lines of raw test logs by correlating the test failure traceback directly with the modified lines in the pull request diff.
2. **Architectural Drift:** Automatically reviews diffs against the repository's internal engineering guidelines, using semantic search over local vector embeddings (`context_harness.json`).
3. **Deterministic Static Analysis Triage:** Ingests SonarQube / SonarCloud reports (SARIF, JSON, or direct Web API), explains complex vulnerabilities, and generates immediate code patches.

### Execution Pipeline (LangGraph)

```mermaid
flowchart TD
    subgraph Inputs["1. Inputs (CI Runner & Environment)"]
        direction TB
        E1["diff.txt (PR Git Diff)"]
        E2["tests.log (Test runner stdout/stderr)"]
        E3["context_harness.json / docs/guidelines.md (Local Vector Index)"]
        E4["sonar-report.json / SARIF / Sonar API (Static Analysis)"]
    end

    subgraph LangGraph["2. LangGraph Orchestration (Parallel Execution)"]
        direction TB
        N1["Node 1: Gemini 2.5 Flash\nTest Failure Triage\n(Correlates logs with diff)"]
        N2["Node 2: Gemini 2.5 Flash\nCode Review (Harness)\n(Semantic match against guidelines)"]
        N3["Node 3: Gemini 2.5 Flash\nSonarQube Remediation\n(Correlates Sonar issues with diff)"]
        N4["Node 4: Gemini 2.5 Pro\nSupervisor & Tech Lead\n(Final verdict + patch synthesis)"]

        N1 --> N4
        N2 --> N4
        N3 --> N4
    end

    subgraph Output["3. Output (GitHub PR Comment)"]
        direction TB
        O1["PR Comment with Tech Lead Verdict"]
        O2["Remediation Patch Code Snippet"]
        O3["SonarQube Triage Section"]
        O4["LLMOps Cost & Telemetry Table"]
    end

    E1 --> N1
    E2 --> N1
    E1 --> N2
    E3 --> N2
    E1 --> N3
    E4 --> N3
    N4 --> Output
```

---

## Context Harness: Local JSON Embeddings

The **Context Harness** transitions the agent from generic coding advice to adhering strictly to your team's specific architecture standards, RFCs, and ADRs.

### Generating the Local Embeddings Index (`context_harness.json`)
You can scan your documentation and generate a local vector embedding index without external vector databases:

```bash
# Using Python locally
python build_harness.py --docs docs README.md --output context_harness.json

# Using Docker
docker compose run --rm harness
```

### How Semantic Retrieval Works
1. `build_harness.py` chunks markdown headings (`## `), computes vector embeddings via Google's `text-embedding-004`, and writes `context_harness.json`.
2. During PR reviews, `gatekeeper.py` computes the embedding of the pull request diff and performs a pure Python cosine similarity search across all stored chunks.
3. Only the top most relevant guidelines (e.g., SQL security, error handling, function size) are injected into the LLM context, keeping token usage low and preventing hallucinations.
4. If `context_harness.json` is not present, the system automatically falls back to reading `docs/guidelines.md` directly.

### Antigravity Skill
An Antigravity skill is included in [`.agents/skills/context-harness/SKILL.md`](file:///.agents/skills/context-harness/SKILL.md). In the Antigravity IDE or CLI, the agent can be prompted to rebuild the harness whenever new RFCs or ADRs are merged.

---

## SonarQube & SonarCloud Integration

The Gatekeeper natively supports SonarQube through three channels:

### 1. File-Based Ingestion (Recommended for CI/CD)
When your CI pipeline runs SonarScanner, configure it to output a report into the workspace:
- **JSON Report:** Place `sonar-report.json` in the workspace root.
- **SARIF Report:** Place `sonar-report.sarif` in the workspace root (standard GitHub Code Scanning format).

### 2. Direct Web API Query
If running in an environment with network access to your SonarQube server, set the following environment variables:
- `SONAR_HOST_URL`: Base URL (e.g., `https://sonarcloud.io` or `http://sonar.internal:9000`).
- `SONAR_TOKEN`: User or project analysis token.
- `SONAR_PROJECT_KEY`: Sonar project identifier.
- `PR_NUMBER`: (Optional) Restricts queries to issues introduced in the active pull request.

`sonar_adapter.py` will query `/api/issues/search`, parse unresolved issues, and feed them into the `sonar_triage` node.

---

## Lean LLMOps & Cost Efficiency

- **Zero Cost on Passing Tests:** If the test output does not contain failure keywords (`FAIL`, `ERROR`, `FAILED`), the diagnostics node skips LLM invocation entirely.
- **Zero Cost when Sonar is Clean:** If SonarQube reports zero issues, the Sonar node skips LLM calls.
- **Dynamic Model Tiering:** High-volume triage runs on `gemini-2.5-flash` ($0.075 / $0.30 per 1M tokens), reserving `gemini-2.5-pro` strictly for final synthesis and decision-making by the supervisor node.
- **Open Cost Accounting:** Every run posts an itemized table in the PR comment showing prompt tokens, completion tokens, execution seconds, and calculated USD cost (typically below `$0.003 USD` per PR).

---

## Repository Structure

```text
ai-gatekeeper/
├── .agents/
│   └── skills/
│       └── context-harness/
│           └── SKILL.md         # Antigravity Agent Skill for indexing guidelines
├── .github/
│   └── workflows/
│       └── gatekeeper.yml       # Official CI/CD workflow
├── docs/
│   ├── guidelines.md            # Repository standards (Context Harness)
│   ├── folder_structure.md      # Detailed folder layout documentation
│   ├── Lean_Canvas_and_MVP_Strategy.md # Lean canvas and MVP roadmap
│   └── Lean Canvas & Estratégia de MVP.pdf # Original MVP canvas document
├── tests/
│   ├── fixtures/                # Sample diffs, logs, and SonarQube reports
│   ├── conftest.py              # Pytest fixtures and mock objects
│   └── test_gatekeeper.py       # Automated unit and integration test suite
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore patterns
├── build_harness.py             # CLI to scan docs and generate local vector index
├── context_harness.py           # Semantic retrieval engine with pure Python cosine similarity
├── docker-compose.yml           # Docker services orchestration
├── Dockerfile                   # Python 3.11 slim container definition
├── gatekeeper.py                # Core LangGraph execution engine
├── pytest.ini                   # Pytest configuration
├── README.md                    # Project documentation & CI/CD setup guide
├── requirements.txt             # Core production dependencies
├── requirements-dev.txt         # Testing and development dependencies
├── simulate_gatekeeper.py       # Local PR scenario simulator with Sonar support
└── sonar_adapter.py             # SonarQube/SonarCloud SARIF, JSON, and Web API adapter
```

---

## Running with Docker

### 1. Configure Environment Variables
Copy the template file and define your Google Gemini API key:
```bash
cp .env.example .env
# Edit .env and supply your GOOGLE_API_KEY
```

### 2. Run the Automated Test Suite
```bash
docker compose run --rm test
```

### 3. Generate the Context Harness Vector Index
```bash
docker compose run --rm harness
```

### 4. Run Local Simulation
Prepare sample input files (`diff.txt`, `tests.log`, and `sonar-report.json`):
```bash
# Simulates a scenario with failing tests, Sonar blockers, and guideline violations
docker compose run --rm simulate
```

Execute the Gatekeeper against the prepared files:
```bash
docker compose run --rm gatekeeper
```

---

## How to Download and Configure in Another Project's CI/CD

To use AI Quality Gatekeeper in another repository (Python, Node.js, Go, Java, Rust, etc.):

### Step 1: Add Guidelines to Target Repository
Create `docs/guidelines.md` in the root of your target project:

```markdown
# Repository Architecture Guidelines

## 1. Security
- Never commit credentials, tokens, or plain-text connection strings (BLOCKER).
- All database queries must be parameterized. No string concatenation in SQL (BLOCKER).

## 2. Quality
- Never leave empty catch/except exception blocks (BLOCKER).
- Functions must not exceed 50 lines of code (WARNING).

## 3. Testing
- New endpoints and domain services must include unit or integration tests (BLOCKER).
```

### Step 2: Add Secrets to Target GitHub Repository
1. In your target repository on GitHub, navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret**.
3. Name: `GOOGLE_API_KEY` (Value from [Google AI Studio](https://aistudio.google.com/)).
4. (Optional) Name: `SONAR_TOKEN` and `SONAR_HOST_URL` if using SonarQube Web API.

### Step 3: Configure CI/CD Workflow in Target Project

Create `.github/workflows/ai-gatekeeper.yml` in your target repository:

```yaml
name: AI Quality Gatekeeper

on:
  pull_request:
    branches: [main, master, develop]

jobs:
  gatekeeper:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Gatekeeper Dependencies
        run: |
          pip install langgraph>=0.2.0 langchain-google-genai>=2.0.0 pydantic>=2.0.0 python-dotenv>=1.0.0

      # Adapt this step to your project test stack
      - name: Run Project Tests
        run: |
          pytest > tests.log 2>&1 || true

      # (Optional) Run SonarScanner and output JSON or SARIF report
      - name: Run SonarQube Scan
        run: |
          # sonar-scanner -Dsonar.issuesReport.html.enable=false -Dsonar.issuesReport.json.enable=true
          echo "Sonar scan placeholder"

      - name: Extract PR Diff
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > diff.txt

      - name: Download and Run Gatekeeper
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
        run: |
          curl -sSL https://raw.githubusercontent.com/JPCalsavara/ai-gatekeeper/main/gatekeeper.py -o gatekeeper.py
          curl -sSL https://raw.githubusercontent.com/JPCalsavara/ai-gatekeeper/main/sonar_adapter.py -o sonar_adapter.py
          curl -sSL https://raw.githubusercontent.com/JPCalsavara/ai-gatekeeper/main/context_harness.py -o context_harness.py
          python gatekeeper.py

      - name: Post PR Comment
        if: always()
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          if [ -f report.md ]; then
            gh pr comment ${{ github.event.pull_request.number }} --body-file report.md
          fi
```
