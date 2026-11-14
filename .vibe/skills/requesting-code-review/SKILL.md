---
name: requesting-code-review
description: Request a structured code review of the current changes before declaring work done. Spawns the repo reviewer subagent.
license: MIT
user-invocable: true
allowed-tools: [read_file, bash, grep, todo, task, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Requesting-code-review skill (superpowers, improved for Vibe reviewer subagent)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Requesting Code Review

Get a two-stage review (spec compliance, then code quality) of the branch.

## Process

1. Show what changed: `git status`, `git diff --stat`, and the full diff for
   files the reviewer must judge.
2. Dispatch the repo reviewer subagent with the `task` tool:
   `config_name = "reviewer"`, and pass the diff summary + the spec/task file
   path. The reviewer is read-only and checks against `.claude/rules/`
   (English-only, `Tam Khang` headers, soft delete, no `.env`, Alembic rules).
3. Also self-review the diff against the original spec: every requirement
   covered? any leftover debug code, TODOs, or hardcoded values?
4. Collect findings, group by severity, fix blockers/majors first, re-run
   verification after each fix.
5. Loop `receiving-code-review` -> fix -> re-verify until verdict is APPROVE.
