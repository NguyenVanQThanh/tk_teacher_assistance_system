---
name: verification-before-completion
description: Prove the work is actually done before telling the user it is. Run this before any "finished" claim.
license: MIT
user-invocable: true
allowed-tools: [read_file, bash, grep, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Verification-before-completion skill (superpowers, improved for Vibe)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Verification Before Completion

A task is not done because the code looks right — it is done when evidence says so.

## Checklist

1. Re-run the exact acceptance scenario from the task/spec (endpoint via curl
   or pytest, UI flow, CLI command) and capture the output.
2. Run the relevant test suites: `cd backend && pytest` and the frontend
   tests/e2e; read results, do not assume.
3. Run linters/formatters (Ruff/Black backend, Prettier frontend) and type/build
   checks where configured.
4. If the schema changed: confirm a NEW Alembic migration exists and
   `alembic upgrade head` runs cleanly in the dev DB.
5. Confirm repo-rule compliance: English-only artifacts, `Tam Khang` headers,
   soft delete only, no `.env` touched, task file header/status updated.
6. Report to the user: what was verified (with the commands run), what was NOT
   verified, then ask for confirmation that the task is complete. After
   confirmation, write the memory file in `.claude/memory/feature|fix/`.

Never say "it should work" — only "verified with <command>" or "not verified".
