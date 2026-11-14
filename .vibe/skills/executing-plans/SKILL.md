---
name: executing-plans
description: Execute an approved plan inline in the current session, task by task, verifying each step. Use when subagent dispatch is not wanted.
license: MIT
user-invocable: true
allowed-tools: [read_file, write_file, edit, bash, grep, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Executing-plans skill (superpowers, improved for Vibe + repo rules)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Executing Plans

Implement an approved plan in this session, one task at a time.

## Process

1. Load the plan (task file in `docs/tasks/` or the todo list) and restate the
   first task.
2. For each task, in order:
   - mark it `in progress` in the todo list / task header;
   - implement the exact change at the exact file paths;
   - run the task's verification step (pytest/ruff/build) and read the output —
     do not assume success;
   - mark it done and move on. Stop only on a real blocker, and report it.
3. Keep every artifact compliant: English-only code/comments/UI, file header
   with `Created By`/`Updated By: Tam Khang`, soft delete only, new Alembic
   migration for schema changes, no `.env` access.
4. Update the task file header (`Status`, `Updated At`) as you go.
5. After the last task: run the full relevant test suite, then hand off to
   `requesting-code-review` and `verification-before-completion`.
