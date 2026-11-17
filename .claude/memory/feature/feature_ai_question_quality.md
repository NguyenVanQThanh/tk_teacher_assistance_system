File Name: feature_ai_question_quality.md
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent

### Summary
Better AI question quality (prompts, deterministic validators, LLM judge), strict part ordering (Part1 MCQ, Part2 true/false, Part3 short answer, continuous numbering), and an answer-key comparison on the review screen for AI exercises.

### Feature Specifications
- Prompts `_SYSTEM_INSTRUCTION`/`_PART_RULES` in services/ai_generator_service.py. Part3 answer: one number, max 4 chars (digits, optional leading '-', decimal ',').
- Validators: `validate_short`, `_content_issue` (banned source references via `_BANNED_META`, non-numeric Part3 stems, banned "all of the above" options). The bare token "context" was removed so English questions pass.
- Judge: `review_batch`/`_call_judge` solves each question without seeing the key; code compares; fail-open on judge errors; `AI_JUDGE_ENABLED` is off in tests. Judge-rejected questions are never persisted.
- Models: generator `AI_MISTRAL_MODEL` default `deepseek-v4-1-flash-1017` (served via the Mistral API, verified ~2-3s); judge `AI_JUDGE_MODEL` default `mistral-medium-latest`. `mistral-large-latest` always emits reasoning chunks (~76s, truncation): do not use. Set both explicitly in the prod `.env`.
- Ordering: `question_order.py` (`PART_RANK`, `question_sort_key`); shuffle only within a part; frontend `sortQuestionsByPart`; draft key `tk_exam_draft_v2_`.
- Answer review: `grading_service.build_answer_key`; `attempt_service.redact_for_owner` reveals the key for non-owner viewers (teacher; access enforced by `get_attempt`), after release, or for a personal AI assignment; shared PRACTICE keeps verdicts but no key; `_persist` rejects missing keys (502 `ERR-EXE-AI_ANSWER_KEY_MISSING`). LaTeX is rendered in the comparison boxes.

### Bug & Feature Context
- Odd or unanswerable AI questions, mixed part order, no correct answer shown on review.
- Failures were caused by the token budget eaten by reasoning chunks (`AI_PART_MAX_TOKENS=3500`, `AI_PART_BATCH_SIZE=5`).

### Solution & Technical Details
- Files: ai_generator_service.py, ai_exercise_service.py, grading_service.py, attempt_service.py, question_order.py, assignment_service.py, pdf_export_service.py, config.py, .env.example; frontend StudentExerciseTakingPage.jsx/.css, ExercisePreviewModal.jsx, utils/questionItems.js.
- Deliberate design: Part3 is numeric-only for all subjects (prompt and validator agree; the answer sheet has 4 cells); exhausted retries raise RuntimeError instead of degrading.
