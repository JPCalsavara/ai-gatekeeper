# Repository Structure

```text
ai-gatekeeper/
├── .github/
│   └── workflows/
│       └── gatekeeper.yml       # 1. Official GitHub Actions CI/CD Pipeline
├── docs/
│   ├── guidelines.md            # 2. Context Harness (Architecture rules & standards)
│   ├── folder_structure.md      # 3. Repository layout documentation
│   └── Lean_Canvas_and_MVP_Strategy.md # 4. Product strategy & lean roadmap
├── tests/
│   ├── fixtures/                # 5. Sample diffs and test logs for local simulation
│   ├── conftest.py              # 6. Pytest test fixtures and mocks
│   └── test_gatekeeper.py       # 7. Automated unit and integration test suite
├── .env.example                 # 8. Environment variable configuration template
├── .gitignore                   # 9. Files ignored by Git
├── docker-compose.yml           # 10. Multi-container orchestration (gatekeeper, test, simulate)
├── Dockerfile                   # 11. Standardized Python container image
├── gatekeeper.py                # 12. Core LangGraph engine, LLM models, and telemetry
├── pytest.ini                   # 13. Pytest configuration
├── README.md                    # 14. Project documentation & CI/CD setup guide
├── requirements.txt             # 15. Core production dependencies
├── requirements-dev.txt         # 16. Development and testing dependencies
└── simulate_gatekeeper.py       # 17. Local CLI simulation runner
```
