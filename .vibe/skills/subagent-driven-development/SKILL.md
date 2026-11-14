---
name: subagent-driven-development
description: Execute an approved plan by dispatching a fresh subagent per task via the Vibe task tool, with a review after each task. Most thorough execution mode.
license: MIT
user-invocable: true
allowed-tools: [read_file, write_file, edit, bash, grep, todo, task, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Subagent-driven-development skill (superpowers, improved for Vibe task tool)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Subagent-Driven Development

Execute a plan with one fresh subagent per task, reviewing each task before the
next starts.

## Process

1. Load the approved plan. Create a todo list with one entry per task.
2. For each task:
   - dispatch a FRESH subagent with the `task` tool. In Mistral Vibe, pass the
     agent profile as `config_name` (e.g. `config_name = "explore"` for
     read-only work; use a coding-capable custom agent for implementation).
     Give the subagent: the task text, exact file paths, the repo rules
     (`repo-rules` skill), and the verification step to run;
   - when it returns, review the diff yourself (`bash` `git diff`, `read_file`)
     — spec compliance first, code quality second;
   - run the verification step in the main session;
   - only then mark the todo done and dispatch the next task.
3. Keep the task file header in `docs/tasks/` updated (`Status`, `Updated At`).
4. After all tasks: full test suite, then `requesting-code-review`
   (spawn `config_name = "reviewer"`) and `verification-before-completion`.

## Why fresh subagents

Each task gets a clean context, so earlier tasks don't pollute later ones and
the main session context stays small.
