# AI Agents Guidelines & Skill Registry

This document guides AI coding assistants (Google Antigravity / AGY, GitHub Copilot, Claude Code, OpenAI GPT / Cursor) operating within this repository.

---

## Agent skills

### Issue tracker

Issues and specs live as GitHub issues under `JPCalsavara/ai-gatekeeper`. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical triage roles mapped to repository labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout with ubiquitous domain vocabulary in `CONTEXT.md` and architecture decisions in `docs/adr/`. See `docs/agents/domain.md`.

---

## Skill Registry

The repository provides modular, cross-agent skills located under `.agents/skills/`:

### Quality Gatekeeper Skills
Skill Name | Path | Purpose
:--- | :--- | :---
**`ai-gatekeeper-reviewer`** | `.agents/skills/ai-gatekeeper-reviewer/SKILL.md` | Master Quality Gate reviewer orchestrating tests, SonarQube, diff analysis, and LangGraph evaluation.
**`sonarqube-runner`** | `.agents/skills/sonarqube-runner/SKILL.md` | Queries SonarQube/SonarCloud issues via REST API or triggers containerized scanner scans.
**`context-harness`** | `.agents/skills/context-harness/SKILL.md` | Extracts repository rules and generates local vector embedding index (`context_harness.json`).

### Engineering & Productivity Skills (Matt Pocock Suite)
Skill Name | Purpose
:--- | :---
**`setup-matt-pocock-skills`** | Scaffolds repository configuration for issue tracker, triage labels, and domain docs.
**`ask-matt`** | Guides agent and developer on which skill to use for any development situation.
**`code-review`** | Performs two-axis code review (Standards + Spec) using parallel sub-agents.
**`grill-me`** / **`grill-with-docs`** | Relentless interactive interview resolving ambiguity and updating domain docs.
**`implement`** | Builds work described by specs or tickets, driving TDD and code review.
**`tdd`** | Test-driven development with red-green-refactor loop.
**`diagnosing-bugs`** | Disciplined debugging loop (failing test -> isolate -> hypothesis -> instrument -> fix).
**`domain-modeling`** | Challenges domain terminology and updates `CONTEXT.md` and ADRs.
**`to-spec`** / **`to-tickets`** | Synthesizes discussion into formal specs and tracer-bullet tickets.
**`triage`** | Moves GitHub issues through canonical triage state machine.
**`improve-codebase-architecture`** | Scans codebase for deepening opportunities and visual architecture reports.
**`wayfinder`** | Plans complex multi-session initiatives as dependency graphs on GitHub issues.
**`resolving-merge-conflicts`** | Resolves git merge conflicts hunk by hunk without aborting.

---

## Universal Review Workflow

Before committing changes or creating a Pull Request, agents must execute the gatekeeper check:

```bash
bash .agents/skills/ai-gatekeeper-reviewer/scripts/run_review.sh --target .
```

To automatically apply remediation patches:
```bash
bash .agents/skills/ai-gatekeeper-reviewer/scripts/run_review.sh --target . --apply-patch
```

To review an external target project from this directory:
```bash
bash .agents/skills/ai-gatekeeper-reviewer/scripts/run_review.sh --target /path/to/project
```

### Review Stages Executed
1. **Tests Execution**: Runs `pytest`, `npm test`, or `go test` and stores outputs in `tests.log`.
2. **Git Diff**: Captures active staged and unstaged code changes in `diff.txt`.
3. **SonarQube Integration**: Queries unresolved issues via API or loads `sonar-report.json`.
4. **Context Harness**: Uses semantic retrieval against repository guidelines.
5. **Supervisor Verdict**: Evaluates findings and renders `APPROVED` or `REJECTED` in `report.md`.

---

## Behavioral Standards
- **Zero Emojis**: Maintain professional technical output without emojis in documentation, code comments, commit messages, or reports.
- **Documentation Language**: All documentation, comments, and reports must be in technical English.
- **Verification**: Ensure all unit tests pass (`docker compose run --rm test pytest`) before completing tasks.
