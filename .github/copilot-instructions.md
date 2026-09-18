# GitHub Copilot Custom Instructions

## Repository Overview
This repository contains the AI Quality Gatekeeper, an autonomous PR reviewer powered by LangGraph, SonarQube static analysis, and Context Harness semantic guidelines retrieval.

## Review Skill
When asked to review code, verify a pull request, or inspect branch changes, invoke or refer to the `ai-gatekeeper-reviewer` skill:
```bash
bash .agents/skills/ai-gatekeeper-reviewer/scripts/run_review.sh --target .
```

## Guidelines & Constraints
- Zero Emojis: Never emit emojis in code, commits, comments, or generated reports.
- English Only: Produce all documentation, explanations, and outputs in clear English.
- Always check that unit tests pass cleanly before completing reviews.
