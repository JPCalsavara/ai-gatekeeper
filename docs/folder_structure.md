# Repository Structure & Component Map

The following tree outlines the complete directory layout and component responsibilities of the AI Quality Gatekeeper system:

```text
ai-gatekeeper/
├── .agents/
│   └── skills/
│       ├── ai-gatekeeper-reviewer/ # Master Quality Gate reviewer orchestrator
│       │   ├── SKILL.md            # Skill specification for AGY, Copilot, Claude, GPT
│       │   └── scripts/
│       │       └── run_review.sh   # Automated review CLI runner (tests, diff, Sonar, gatekeeper)
│       ├── sonarqube-runner/       # SonarQube & SonarCloud static analysis runner
│       │   ├── SKILL.md            # Sonar runner specification
│       │   └── scripts/
│       │       └── run_sonar.sh    # Sonar REST API query & Docker scan utility
│       └── context-harness/        # Local JSON vector index builder
│           └── SKILL.md            # Guidelines indexing skill specification
├── .github/
│   ├── workflows/
│   │   └── gatekeeper.yml          # GitHub Actions CI/CD automated review pipeline
│   └── copilot-instructions.md     # GitHub Copilot custom workspace instructions
├── docs/
│   ├── capabilities_and_roadmap.md # Technical capabilities, limitation analysis & roadmap
│   ├── guidelines.md               # Repository engineering standards (Context Harness)
│   ├── folder_structure.md         # Repository layout and component map (this document)
│   ├── Lean_Canvas_and_MVP_Strategy.md # Business model, MVP scope & execution milestones
│   └── Lean Canvas & Estratégia de MVP.pdf # Original MVP canvas reference document
├── tests/
│   ├── fixtures/                   # Sample diffs, logs, and SonarQube reports
│   │   ├── sample_diff.txt         # Clean and blocker git diff samples
│   │   ├── sample_tests.log        # Passing and failing test suite logs
│   │   └── sonar_report.json       # Mock SonarQube issues report
│   ├── conftest.py                 # Pytest fixtures and mock objects
│   └── test_gatekeeper.py          # Automated unit and integration test suite (12 tests)
├── AGENTS.md                       # Universal AI agent guidelines and skill registry
├── CLAUDE.md                       # Claude Code assistant commands and guidelines
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git ignored files and cache patterns
├── build_harness.py                # CLI to scan docs and generate local vector index
├── context_harness.py              # Semantic retrieval engine with pure Python cosine similarity
├── docker-compose.yml              # Container orchestration (gatekeeper, test, simulate, harness)
├── Dockerfile                      # Standardized Python 3.11 container image
├── gatekeeper.py                   # Core LangGraph execution engine, multi-agent nodes & telemetry
├── pytest.ini                      # Pytest configuration
├── README.md                       # Project overview, SonarQube .env guide & CI/CD setup
├── requirements.txt                # Core production runtime dependencies
├── requirements-dev.txt            # Testing and development dependencies
├── simulate_gatekeeper.py          # Local CLI scenario simulator (clean, violation, test failure)
└── sonar_adapter.py                # SonarQube/SonarCloud REST API, JSON, and SARIF adapter
```
