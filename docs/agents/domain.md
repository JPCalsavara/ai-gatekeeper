# Domain Docs

How engineering and review skills should consume this repository's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root.
- **`docs/adr/`** — read ADRs that touch the area you are about to work in.
- **`docs/guidelines.md`** — read engineering architecture guidelines.

If any of these files do not exist, proceed silently. The `/domain-modeling` skill creates them when terms or decisions are resolved.

## File structure

Single-context repository layout:

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-langgraph-for-orchestration.md
│   └── 0002-multi-provider-llm-factory.md
├── docs/agents/
│   ├── domain.md
│   ├── issue-tracker.md
│   └── triage-labels.md
└── src/ (or root modules)
```

## Use the glossary's vocabulary

When output names a domain concept (in an issue title, a refactor proposal, a test name, or a gatekeeper review finding), use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

## Flag ADR conflicts

If proposed changes contradict an existing ADR, surface it explicitly rather than silently overriding.
