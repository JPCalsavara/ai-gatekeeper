# AI Agents Guidelines & Skill Registry

This document guides AI coding assistants (Google Antigravity / AGY, GitHub Copilot, Claude Code, OpenAI GPT / Cursor) operating within this repository.

---

## Skill Registry

The repository provides modular, cross-agent skills located under `.agents/skills/`:

Skill Name | Path | Purpose
:--- | :--- | :---
**`ai-gatekeeper-reviewer`** | `.agents/skills/ai-gatekeeper-reviewer/SKILL.md` | Master Quality Gate reviewer orchestrating tests, SonarQube, diff analysis, and LangGraph evaluation.
**`sonarqube-runner`** | `.agents/skills/sonarqube-runner/SKILL.md` | Queries SonarQube/SonarCloud issues via REST API or triggers containerized scanner scans.
**`context-harness`** | `.agents/skills/context-harness/SKILL.md` | Extracts repository rules and generates local vector embedding index (`context_harness.json`).

---

## Universal Review Workflow

Before committing changes or creating a Pull Request, agents must execute the gatekeeper check:

```bash
bash .agents/skills/ai-gatekeeper-reviewer/scripts/run_review.sh --target .
```

To review an external target project from this directory:
```bash
bash .agents/skills/ai-gatekeeper-reviewer/scripts/run_review.sh --target /path/to/project
```

### Review Stages Executed
1. **Tests Execution**: Runs `npm test`, `pytest`, or `go test` and stores outputs in `tests.log`.
2. **Git Diff**: Captures active staged and unstaged code changes in `diff.txt`.
3. **SonarQube Integration**: Queries unresolved issues via API or loads `sonar-report.json`.
4. **Context Harness**: Uses semantic retrieval against repository guidelines.
5. **Supervisor Verdict**: Evaluates findings and renders `APPROVED` or `REJECTED` in `report.md`.

---

## Behavioral Standards
- **Zero Emojis**: Maintain professional technical output without emojis in documentation, code comments, commit messages, or reports.
- **Documentation Language**: All documentation, comments, and reports must be in technical English.
- **Verification**: Ensure all unit tests pass (`pytest` in Docker or local runner) before completing tasks.
