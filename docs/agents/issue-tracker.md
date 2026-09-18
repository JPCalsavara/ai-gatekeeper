# Issue Tracker: GitHub

Issues and specs for this repository live as GitHub issues under `JPCalsavara/ai-gatekeeper`. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repository automatically from `git remote -v`.

## Pull Requests as a Triage Surface

**PRs as a request surface: no.**

When reviewing pull requests, use `ai-gatekeeper-reviewer` or `code-review`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue using `gh issue create`.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Wayfinding Operations

Used by `/wayfinder`. The **map** is a single issue with child issues as tickets:

- **Map**: a single issue labelled `wayfinder:map`, holding Notes, Decisions-so-far, and Fog body (`gh issue create --label wayfinder:map`).
- **Child ticket**: an issue linked to the map with `Part of #<map>` in the body and labelled `wayfinder:<type>`.
- **Claim**: `gh issue edit <n> --add-assignee @me`.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append summary to the map issue.
