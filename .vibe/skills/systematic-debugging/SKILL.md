---
name: systematic-debugging
description: Four-phase root-cause debugging. Use for any bug, failing test or unexpected behavior before changing code.
license: MIT
user-invocable: true
allowed-tools: [read_file, write_file, edit, bash, grep, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Systematic-debugging skill (superpowers, improved for Vibe + repo rules)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Systematic Debugging

Never guess-fix. Work the root cause in four phases.

## Phase 1 — Reproduce

- Run the failing behavior yourself (`bash`: pytest case, curl the endpoint,
  build the frontend) and capture the exact error, stack trace and logs.
- Note the environment (branch, commit, how the app is run: docker-compose or
  local). Write the repro steps into the todo list.

## Phase 2 — Locate

- Read the stack trace top-down; identify the first frame in OUR code
  (`backend/app/...`, `frontend/src/...`).
- `grep` for the error message / symbol to find all related call sites.
- Add temporary structured logging (plain text, no emojis) if needed to see
  actual values at runtime.

## Phase 3 — Root cause

- Form a hypothesis, then prove or disprove it with a minimal experiment
  (a focused pytest, a REPL snippet, a curl). Do not stack multiple changes.
- Ask "why" until you reach the actual cause, not a symptom. Check recent
  changes: `git log` / `git blame` on the suspect file.

## Phase 4 — Fix & verify

- Implement the smallest correct fix. English-only code, `Tam Khang` header,
  structured error handling (no swallowed exceptions).
- Schema involved? New Alembic migration. Deletion involved? Soft delete only.
- Re-run the repro — it must pass — plus the surrounding test suite
  (`backend/tests`, frontend tests) to catch regressions.
- Update the task/memory docs, then ask the user for confirmation and write the
  `.claude/memory/fix/bugfix_*.md` file after confirmation.
