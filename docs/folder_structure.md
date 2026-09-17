# Repository Structure

```text
ai-gatekeeper/
├── .agents/
│   └── skills/
│       └── context-harness/
│           └── SKILL.md         # 1. Antigravity Agent Skill for indexing guidelines
├── .github/
│   └── workflows/
│       └── gatekeeper.yml       # 2. Official GitHub Actions CI/CD Pipeline
├── docs/
│   ├── guidelines.md            # 3. Context Harness (Architecture rules & standards)
│   ├── folder_structure.md      # 4. Repository layout documentation
│   ├── Lean_Canvas_and_MVP_Strategy.md # 5. Product strategy & lean roadmap
│   └── Lean Canvas & Estratégia de MVP.pdf # 6. Original MVP canvas document
├── tests/
│   ├── fixtures/                # 7. Sample diffs, logs, and SonarQube reports
│   ├── conftest.py              # 8. Pytest fixtures and mocks
│   └── test_gatekeeper.py       # 9. Automated unit and integration test suite
├── .env.example                 # 10. Environment variable configuration template
├── .gitignore                   # 11. Files ignored by Git
├── build_harness.py             # 12. CLI to scan docs and generate local vector index
├── context_harness.py           # 13. Semantic retrieval engine with pure Python cosine similarity
├── docker-compose.yml           # 14. Multi-container orchestration (gatekeeper, test, simulate, harness)
├── Dockerfile                   # 15. Standardized Python container image
├── gatekeeper.py                # 16. Core LangGraph engine, LLM models, and telemetry
├── pytest.ini                   # 17. Pytest configuration
├── README.md                    # 18. Project documentation & CI/CD setup guide
├── requirements.txt             # 19. Core production dependencies
├── requirements-dev.txt         # 20. Development and testing dependencies
├── simulate_gatekeeper.py       # 21. Local CLI simulation runner with Sonar support
└── sonar_adapter.py             # 22. SonarQube/SonarCloud SARIF, JSON, and Web API adapter
```
