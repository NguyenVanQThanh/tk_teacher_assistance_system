---
name: writing-plans
description: Write an implementation plan of bite-sized tasks (2-5 min each) with exact file paths and verification steps, based on an approved design.
license: MIT
user-invocable: true
allowed-tools: [read_file, grep, write_file, bash, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Writing-plans skill (superpowers, improved for Vibe + repo rules)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Writing Plans

Turn an approved design into a plan of small, verifiable tasks. No task should
take more than ~5 minutes.

## Process

1. Re-read the approved spec (from `brainstorming`) and the relevant code.
2. Break work into tasks. Every task MUST specify:
   - exact file paths to create/modify (e.g. `backend/app/modules/exercise/router.py`);
   - the concrete change (what code/logic goes where);
   - a verification step (test command, `pytest` path, `ruff`, build, manual
     check) — verification must be runnable, not "check it works";
   - dependencies on earlier tasks.
3. Order tasks so each leaves the repo in a working state (tests green).
4. Save the plan as a task file under `docs/tasks/<spec>/` with the standard
   header (`Slice`, `Type`, `Size`, `SP`, `Depends on`, `Status: draft`,
   `Created By: Tam Khang`) and one section per task, or as a `todo` list if
   the plan is executed in this session.
5. Include the repo-rule tasks explicitly when relevant: new Alembic migration
   for schema changes, English-only artifacts with `Tam Khang` headers, soft
   delete flags instead of hard deletes, memory file at the end.
6. Ask the user to approve the plan. Then hand off to
   `subagent-driven-development` or `executing-plans`.
