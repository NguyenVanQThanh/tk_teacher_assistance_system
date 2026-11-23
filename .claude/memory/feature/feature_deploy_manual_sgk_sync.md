File Name: feature_deploy_manual_sgk_sync.md
Created At: 2026-11-14
Created By: AI Agent
Updated At: 2026-11-14
Updated By: AI Agent

### Summary
Deploy workflow is now manual-only, gated by the ci workflow, and syncs SGK RAG data from Google Drive only when the version changes.

### Feature Specifications
- Trigger: `workflow_dispatch` only (no push to `prod`). Input `force_sgk` forces SGK re-download.
- Gate: job `test` calls `ci.yml` (`workflow_call`); `build-and-push` needs it. ci.yml runs pytest (3 tests deselected) + frontend build. Playwright e2e is NOT in the gate.
- SGK sync: repo Variables `SGK_DRIVE_FOLDER_ID` and `SGK_VERSION`. Step compares `SGK_VERSION` with `$DEPLOY_PATH/sgk_data/.version` on the server; equal => skip. Different/missing => `gdown --folder`, scp `vectors.dump` + `images.tar`, write `.reload` and `.version`.
- Reload: `remote-deploy.sh` sees `sgk_data/.reload`, runs `TRUNCATE chunks`, clears `/app/uploads/sgk_images`, `up -d --force-recreate`; then removes the flag. Needed because `load_sgk.sh` loads only into empty targets.
- Hard delete of `chunks` explicitly approved by the user (rebuildable index, exception to soft-delete policy).
- Deploy job timeout raised 15 -> 30 min (2 GB download + scp).
- Separate step "Verify SSH access and target directory" gives clearer errors.

### Bug & Feature Context
- Not a bug fix. Server state at time of work: `/home/thanhnvq/smartlms` had only `deploy/` and `postgres-init/`; no `sgk_data`, no `smartlms_backend` container (first deploy), so first run downloads 2 GB from Drive automatically.

### Solution & Technical Details
- Files: `.github/workflows/deploy.yml`, `.github/workflows/ci.yml`, `deploy/scripts/remote-deploy.sh`, `D:\Code\RAG_SGK\README.md` (section "Publish a new RAG_SGK version").
- Publishing a new RAG_SGK version: replace files in Drive, bump `SGK_VERSION`, run deploy.
- Risks: healthcheck waits 120 s, first SGK load may exceed it (re-run workflow); RAG empty briefly during reload; gdown may hit Drive quota (fallback: R2); Drive files must be named exactly `vectors.dump` / `images.tar`, shared "Anyone with the link".
- Open: add e2e job to the gate if wanted.
