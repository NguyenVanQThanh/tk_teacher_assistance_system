---
name: brainstorming
description: Turn a rough idea into a concrete, reviewable spec before any code. Use when the user says "let's build/add X" or the requirement is unclear.
license: MIT
user-invocable: true
allowed-tools: [read_file, grep, bash, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Brainstorming skill (superpowers, improved for Vibe + repo rules)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Brainstorming

Refine a raw idea into a spec in small chunks the user can actually read.
Do NOT write code in this phase.

## Process

1. Restate the goal in one sentence and confirm understanding with
   `ask_user_question`.
2. Explore the existing codebase first (`grep`, `read_file`): find the modules,
   patterns and conventions in `backend/app/modules/` / `frontend/src/` that
   this idea touches. Reuse them; do not invent parallel patterns.
3. Ask clarifying questions one at a time (edge cases, non-goals, data model
   impact, UI vs API). Use `ask_user_question` with 2-4 options each.
4. Propose the design in chunks: data model -> API -> UI -> migration -> tests.
   Pause after each chunk for approval.
5. Schema change? State that a NEW Alembic migration will be created (never edit
   applied migrations). Deletion involved? State it will be soft delete only.
6. Write the approved spec to `docs/tasks/<spec>/` as a draft task file with
   the standard header (`Status: draft`, author `Tam Khang`) unless the user
   wants it elsewhere.
7. End by asking: "Approve this design so I can write the plan?" Only then
   hand off to `writing-plans`.

## Rules that always apply

English-only code/artifacts, `Tam Khang` headers, soft delete only, no `.env`
access, verify claims by running things.
