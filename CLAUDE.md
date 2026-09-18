# Claude Code Assistant Guidelines

This repository implements the AI Quality Gatekeeper with LangGraph dynamic model tiering, Context Harness semantic search, and SonarQube static analysis.

## Key Commands

- **Run Quality Gatekeeper Review**:
  ```bash
  bash .agents/skills/ai-gatekeeper-reviewer/scripts/run_review.sh --target .
  ```
- **Run Unit Tests (Docker)**:
  ```bash
  docker compose run --rm test pytest -v --tb=short
  ```
- **Build Context Harness Embeddings**:
  ```bash
  python build_harness.py --docs docs README.md --output context_harness.json
  ```
- **Fetch SonarQube Issues via API**:
  ```bash
  bash .agents/skills/sonarqube-runner/scripts/run_sonar.sh --target . --api
  ```

## Rules & Standards
- Strictly zero emojis across all generated code, comments, reports, and documentation.
- All documentation and commits must be in technical English.
- Always run `pytest` before finalizing any PR or commit.
