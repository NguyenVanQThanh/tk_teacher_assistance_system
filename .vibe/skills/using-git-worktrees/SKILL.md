---
name: using-git-worktrees
description: Start isolated work in a git worktree on a new branch, run setup, and verify a clean baseline before coding.
license: MIT
user-invocable: true
allowed-tools: [bash, read_file, grep, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Using-git-worktrees skill (superpowers, improved for Vibe + this monorepo)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Using Git Worktrees

Keep parallel work isolated from the main checkout.

## Process

1. Pick a branch name (`feat/<spec>` / `fix/<bug>`). Never work directly on
   `main`/`dev` for a feature.
2. Create the worktree: `git worktree add ../<repo>-<branch> -b <branch>`
   (from the repo root; adjust the path outside the main tree).
3. Setup inside the worktree: backend venv + `pip install -r backend/requirements.txt`,
   frontend `npm ci` if needed; copy `.env.example` to `.env` manually if the
   user needs a local run — NEVER read or copy a real `.env`.
4. Verify the baseline is clean: run the backend test suite (`pytest`) and
   frontend checks in the worktree BEFORE making changes. Record the result.
5. Implement the plan (see `executing-plans` / `subagent-driven-development`),
   committing with descriptive messages.
6. When done, hand off to `finishing-a-development-branch`.
