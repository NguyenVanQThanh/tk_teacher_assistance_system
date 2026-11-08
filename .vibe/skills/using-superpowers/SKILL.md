---
name: using-superpowers
description: Entry point of the superpowers workflow adapted for Mistral Vibe. Use at the start of any new feature or bug fix to pick the right process skill before writing code.
license: MIT
user-invocable: true
allowed-tools: [read_file, grep, bash, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Superpowers bootstrap skill adapted for Mistral Vibe in this repo
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Using Superpowers (Vibe edition)

Improved port of obra/superpowers for Mistral Vibe: process skills set the
approach first, then implementation happens. Never jump straight into code.

## Decision table

- "Let's build / add / implement X" -> invoke `brainstorming` first, then
  `writing-plans`, then `subagent-driven-development` (or `executing-plans`).
- "Fix this bug / it's broken" -> invoke `systematic-debugging` first.
- "Review my changes" -> invoke `requesting-code-review`.
- "The review came back with comments" -> invoke `receiving-code-review`.
- "I think we're done" -> invoke `verification-before-completion` before
  telling the user it works.
- Writing tests for new logic -> `test-driven-development`.
- Starting isolated work on a branch -> `using-git-worktrees`, and
  `finishing-a-development-branch` when done.

## Vibe-specific notes

- Skills are invoked with `/<skill-name>` in an interactive session, or loaded
  automatically when the description matches the task.
- Subagents are spawned with the `task` tool using `config_name`
  (e.g. `config_name = "reviewer"` for the repo reviewer, `"explore"` is built in).
- Repo rules always apply on top: see the `repo-rules` skill (English-only code,
  `Tam Khang` file headers, soft delete only, new Alembic migration per schema
  change, task files in `docs/tasks/`, memory file in `.claude/memory/` after
  user confirmation).
