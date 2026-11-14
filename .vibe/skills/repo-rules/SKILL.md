---
name: repo-rules
description: Condensed rules of this repo (from .agents/AGENTS.md and .claude/rules/). Load this skill whenever you code, review, document or finish a task here.
license: MIT
user-invocable: true
allowed-tools: [read_file, grep, bash, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Repo rules skill distilled from .agents/AGENTS.md + .claude/rules for Mistral Vibe
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Repo Rules (SmartLMS)

Source of truth: `.agents/AGENTS.md`, `.claude/rules/coding_rules.md`,
`.claude/rules/memory_and_completion_rules.md`. Summary:

1. Before coding/analysis, read those rule files (or trust this skill).
2. Every new/updated file starts with a header: `File Name`, `Description`,
   `Created At`, `Created By`, `Updated At`, `Updated By` — author fields MUST be
   `Tam Khang` (never "AI Agent").
3. Code, names, comments, docstrings, UI text, labels, error messages, logs:
   Standard English. No emojis/icons in logs.
4. Never read/modify `.env` or secret files (also blocked by `.vibe/config.toml`
   denylist). Use env injection / secrets manager.
5. Soft delete ONLY (`status = DELETED` / soft-delete flag). Hard delete is
   prohibited; convert any spec that requires it.
6. Schema change => NEW Alembic migration (`alembic revision --autogenerate`).
   Never edit already-applied migrations.
7. Task files in `docs/tasks/<spec>/<task>.md` keep header (`Path`, `Slice`,
   `Type`, `Size`, `SP`, `Depends on`, `Status`, `Created At`, `Updated At`) and
   status flow `draft` -> `in progress` -> `ready to test` -> `done`.
8. On completion: ask the user for confirmation; after confirmation write a
   memory file in `.claude/memory/feature/` or `.claude/memory/fix/` with
   sections Summary / Feature Specifications / Bug & Feature Context /
   Solution & Technical Details.
9. Architecture: monorepo `backend/` (FastAPI, SQLAlchemy 2.0, Alembic,
   PostgreSQL, JWT) + `frontend/` (React 18, Vite). Keep business logic in
   `backend/app/modules/`, separate from framework code.
10. Verify before claiming done (run tests/lint/build); state what was and was
    not verified. Reply to the user in Vietnamese.
11. Never run `git commit` yourself. Only `git add` the changed files and hand
    the user a ready-to-paste commit message — the user commits.
