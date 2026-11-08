<!-- File Name: project-rules.md
Description: System prompt for Mistral Vibe in this repo — consolidated from .agents/AGENTS.md and .claude/rules/
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

You are running inside Mistral Vibe on the SmartLMS monorepo (`backend/` FastAPI +
PostgreSQL/Alembic, `frontend/` React 18 + Vite). Reply to the user in Vietnamese;
all code, comments, identifiers, UI text and logs stay in Standard English.

Apply these project rules on every task (source: `.agents/AGENTS.md`,
`.claude/rules/coding_rules.md`, `.claude/rules/memory_and_completion_rules.md`):

1. **Read the rules first.** Before any coding/analysis task, read
   `.claude/rules/coding_rules.md` and `.claude/rules/memory_and_completion_rules.md`
   (or load the `/repo-rules` skill) and follow them strictly.
2. **File header.** Every new/updated code, doc or task file starts with a header:
   `File Name`, `Description`, `Created At` (YYYY-MM-DD), `Created By`,
   `Updated At`, `Updated By`. Author fields MUST be `Tam Khang` — never "AI Agent".
3. **Language.** Code, variable/function names, comments, docstrings, UI labels,
   error messages and logs are Standard English. No emojis/icons in log statements.
4. **Secrets.** Never read, modify or interact with `.env` or any file containing
   secrets (enforced in `.vibe/config.toml` via bash/read_file denylist).
5. **Soft delete only.** All deletions are soft deletes (`status = DELETED` or a
   soft-delete flag). Hard delete is strictly prohibited; convert any spec that
   asks for it.
6. **Database.** Every schema change requires a NEW Alembic migration
   (`alembic revision --autogenerate -m "..."`). Never edit migrations that were
   already applied.
7. **Task files.** Task files in `docs/tasks/` carry a header (`Path`, `Slice`,
   `Type`, `Size`, `SP`, `Depends on`, `Status`, `Created At`, `Updated At`) with
   status `draft` -> `in progress` -> `ready to test` -> `done`. Update `Status`
   and `Updated At` on every change.
8. **Completion & memory.** When a feature/fix is implemented, ask the user for
   confirmation first. After confirmation, write a memory file in
   `.claude/memory/feature/` or `.claude/memory/fix/` with the header above and
   sections: Summary, Feature Specifications, Bug & Feature Context,
   Solution & Technical Details.
9. **Workflow skills.** For new work prefer the superpowers flow:
   `/brainstorming` -> `/writing-plans` -> `/subagent-driven-development` (or
   `/executing-plans`) -> `/requesting-code-review` ->
   `/verification-before-completion`. For bugs use `/systematic-debugging`.
10. **Verification.** Never claim something works without running it (tests,
    build, lint). State clearly what was verified and what was not.
11. **Git commits.** NEVER run `git commit` yourself. Only `git add` the
    relevant files and hand the user a ready-to-paste commit message; the user
    performs the commit. This applies even when the user asks to "add and
    commit" — in that case add the files and propose the message only.
