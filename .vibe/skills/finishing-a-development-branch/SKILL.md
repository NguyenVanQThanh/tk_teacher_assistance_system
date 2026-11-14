---
name: finishing-a-development-branch
description: Finish a branch properly — full verification, review, merge/rebase flow and worktree cleanup.
license: MIT
user-invocable: true
allowed-tools: [bash, read_file, grep, todo, task, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Finishing-a-development-branch skill (superpowers, improved for Vibe)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Finishing a Development Branch

Close out a feature/fix branch cleanly.

## Process

1. Run FULL verification in the worktree/branch: backend `pytest`, frontend
   tests/e2e, linters, and `alembic upgrade head` if a migration was added.
   Fix anything red; never merge a red branch.
2. Update the task file(s) in `docs/tasks/` to `ready to test` (or `done` after
   user confirmation) with `Updated At` refreshed.
3. Request review (`requesting-code-review`, reviewer subagent) and resolve
   findings (`receiving-code-review`) until APPROVE.
4. Sync with the base branch (`git fetch` + rebase onto `dev`, resolving
   conflicts; run tests again after rebase). Push the branch (push needs user
   approval in this harness — ask first).
5. Open a PR with a summary of changes + verification evidence; link the task
   file. Merge only after user confirmation and green checks.
6. Cleanup: `git worktree remove` the worktree once merged/abandoned; delete
   the remote branch if applicable.
7. After user confirms completion, write the memory file in
   `.claude/memory/feature|fix/` per `repo-rules`.
