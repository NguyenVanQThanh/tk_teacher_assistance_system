File Name: bugfix_document_pr_review_split.md
Created At: 2026-11-05
Created By: AI Agent
Updated At: 2026-11-05
Updated By: AI Agent

### Summary
PR #24 (`fix/Teacher_documentaries`, feat(document) inline PDF viewing) was rejected by the AI review bot (real findings, then a "veto: diff too large" rejection). Real findings were fixed and the work was split into three small PRs against `dev`. All were approved and merged.

### Feature Specifications
- `GET /api/v1/documents/{id}/view` streams PDF/images inline; every other file type is served as `attachment`. Does not increment the download counter.
- Document preview modal has only a Close button. Download and print come from the native PDF toolbar. No custom Download button remains in the modal (including error and non-PDF states).
- `EditDocumentModal` is metadata-only (title, subject, document type) for documents.
- Exercise question editor (LaTeX toolbar, add/edit/delete questions, backend sync) lives in `EditExerciseModal`, used only by `ExerciseRepositoryPage`.

### Bug & Feature Context
- The original PR rewrote `EditDocumentModal` into a metadata-only form and deleted the exercise question editor still used by `ExerciseRepositoryPage` (regression).
- Download/Print buttons were commented out in the preview modal; the user wanted them removed, not commented.
- `docType` was initialised from `doc.fileType`, but the list mapping uses `fileType` as the document type (lecture/exam/reference), not the file extension (`fileExtension`).
- Moved exercise editor was reviewed as new code: early `return null` before hooks (hook-count crash), save errors swallowed and modal closed, state not reset between exercises, undefined `setLastInserted`.
- Bot vetoes any PR with a very large diff (+/- thousands of lines). Compare against the PR base (`dev`), not `main`. `fetch failed` after veto is a transient runner network error.

### Solution & Technical Details
- Split into branches off `dev`:
  - `fix/exercise_editor_extract` (PR #25): `frontend/src/components/documents/EditExerciseModal.jsx/.css`, `frontend/src/pages/teacher/ExerciseRepositoryPage.jsx`. `EditExerciseModal` is a wrapper that returns null when closed and renders `EditExerciseModalInner` with `key` = exercise id, so hooks are unconditional and state resets per exercise. Save errors keep the modal open and show an alert; `isSaving` always reset.
  - `fix/document_preview_view`: `backend/app/modules/document/routers/documents.py` (disposition inline only for PDF/images), `DocumentPreviewModal.jsx/.css`, `DocumentCard.jsx`, `DocumentDetailView.jsx/.css`, `DocumentRepositoryPage.jsx`, `frontend/src/services/api.js` (`documentsApi.viewDocument`, blob), backend test.
  - `fix/document_edit_modal_slim`: `EditDocumentModal.jsx/.css`, `DocumentRepositoryPage.jsx` (sends `document_type` on update).
- Lessons: keep PRs small (bot limit); no force push or `reset --hard` without permission; commits in this repo must not include a Co-Authored-By line (user instruction).
