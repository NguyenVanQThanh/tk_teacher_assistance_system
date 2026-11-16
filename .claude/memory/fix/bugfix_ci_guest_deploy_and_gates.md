File Name: bugfix_ci_guest_deploy_and_gates.md
Created At: 2026-11-16
Created By: AI Agent
Updated At: 2026-11-16
Updated By: AI Agent

### Summary
CI/CD updated so guest-account configuration deploys automatically, and two new CI gates were added. Also records the earlier CI breakage after the Mistral-only change and the merge workflow lessons.

### Feature Specifications
- `deploy.yml` now forwards these GitHub Actions **Variables** (not secrets) into `deploy/.env.prod` on the server: `TRUST_PROXY_HEADERS`, `TRUSTED_PROXY_HOPS`, `GUEST_ACCESS_ENABLED`, `GUEST_CREATE_PER_IP_HOUR`, `GUEST_CREATE_GLOBAL_HOUR`, `GUEST_AI_LIMIT`, `GUEST_DOC_LIMIT`. An unset or empty variable keeps whatever is already in `.env.prod`.
- `deploy/.env.prod.example` documents the same keys (defaults: proxy trust true, hops 1, caps 5/200/3/3).
- `ci.yml` new gates: exactly one Alembic head (`alembic heads | grep -c '(head)'` must be 1) and `node frontend/src/utils/errorMessages.selfcheck.mjs`.

### Bug & Feature Context
- CI failure on `fix/ai-use-mistral-only`: tests still mocked Gemini after generation became Mistral-only. Fixed by mocking `_call_mistral_part` and setting `MISTRAL_API_KEY` (also in `test_guest.py` after PR #70).
- A second Alembic head (notifications vs phone migration) once broke deploy (#69); the new CI gate prevents it.
- `ERR-XXX-YYY` codes raised in backend without a Vietnamese mapping fail the selfcheck; the new gate catches it before merge.
- Squash merge of PR #72 rewrote commit hashes, so the stacked frontend branch needed `git rebase --onto origin/dev <old-base> <branch>` then `git push --force-with-lease`.

### Solution & Technical Details
- Files: `.github/workflows/deploy.yml`, `.github/workflows/ci.yml`, `deploy/scripts/remote-deploy.sh` (header comment only; its merge loop already writes any key from `.deploy.env`), `deploy/.env.prod.example`.
- Set a variable: GitHub repo > Settings > Secrets and variables > Actions > Variables tab (or `gh variable set TRUST_PROXY_HEADERS --body true`). Must be set before the next push to `prod` for guests to work behind Cloudflare Tunnel.
- Pre-existing note in `ci.yml`: 3 grading tests are `--deselect`ed (ponytail comment); remove once fixed.
- Deploy runs `alembic upgrade head` via `backend/docker/migrate.sh`; `bootstrap_admin.py` runs `seed_rbac`, so no manual RBAC seed is needed. Guest allow-list lives in code, not in the DB.
- The bot veto (diff too large, 62+ files) was handled by splitting PRs; plan for PRs under roughly 1000 lines.
