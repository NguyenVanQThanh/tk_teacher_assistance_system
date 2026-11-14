---
name: test-driven-development
description: Red -> green -> refactor for new business logic in this repo (pytest for backend, frontend test runner for frontend).
license: MIT
user-invocable: true
allowed-tools: [read_file, write_file, edit, bash, grep, todo]
---

<!-- File Name: SKILL.md
Description: TDD skill (superpowers, improved for Vibe + repo test layout)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Test-Driven Development

Use for new core business logic in `backend/app/modules/` and new frontend
behavior.

## Loop

1. **RED** — write one failing test that captures the exact expected behavior.
   Backend: add a case under `backend/tests/` (pytest, config in
   `backend/pytest.ini`). Frontend: under `frontend/src/` next to the component
   or in `frontend/e2e/`. Run it; confirm it fails for the RIGHT reason.
2. **GREEN** — implement the minimal code to make it pass. No extra features.
   Follow repo rules: English-only, `Tam Khang` header, soft delete only,
   structured exceptions, new Alembic migration if the schema changes.
3. **REFACTOR** — clean up while keeping tests green. Run the linter/formatter
   used by the repo (Ruff/Black for Python, Prettier for frontend).
4. Repeat for the next behavior. Run the whole module's test suite at the end:
   `cd backend && pytest` (or the frontend runner), and read the output.

## Anti-patterns to avoid

- Tests that only assert "no exception" for complex logic.
- Mocking everything so the test proves nothing.
- Skipping the RED phase — always see the test fail first.
