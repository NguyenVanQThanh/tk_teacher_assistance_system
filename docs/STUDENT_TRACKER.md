<!--
File Name: STUDENT_TRACKER.md
Description: Comprehensive tracker for Student role use cases across Backend, Frontend, and Testing.
Created At: 2026-09-30
Created By: Tam Khang
Updated At: 2026-09-30
Updated By: Tam Khang
-->

# Student Role Use Cases Tracker

> Path: `docs/STUDENT_TRACKER.md` · Role: **Student (Học sinh)**  
> Created By: `Tam Khang` · Updated By: `Tam Khang` · Updated At: `2026-09-30`  
> Scope: Self-study dashboard, competency assessment, assignments feed, standalone exam taking, AI self-practice, score history.

| Use Case | BE | FE | Test |
| :--- | :---: | :---: | :---: |
| **1. Authentication & Profile** | | | |
| Student authentication with phone/email and password (`POST /api/v1/auth/login`) | [x] | [x] | [x] |
| Student profile retrieval with enrolled class and student code (`GET /api/v1/auth/me`) | [x] | [x] | [x] |
| Change student account password (`POST /api/v1/auth/change-password`) | [x] | [x] | [x] |
| Secure session logout and token revocation (`POST /api/v1/auth/logout`) | [x] | [x] | [x] |
| Protected Student routing & persistent student layout guard (`StudentLayout`) | [x] | [x] | [x] |
| **2. Student Dashboard & Self-Evaluation (`/student` or `/student/dashboard`)** | | | |
| Weekly study schedule and class timetable widget | | | |
| Core study metrics: Completed exercises count, overall accuracy rate, study time | | | |
| Multi-subject competency spider / radar chart (Biểu đồ mạng nhện đánh giá năng lực đa môn) | | | |
| Automated qualitative feedback commentary on student learning capability & strengths/weaknesses | | | |
| Upcoming assignment deadlines countdown banner & urgent feed | [x] | | |
| AI Self-Practice Generator Modal: Choose subject & topic to generate practice quiz | | | |
| Quick access to recent exercise attempts and performance trends | [x] | | |
| **3. Assigned Exercises & Homework Feed (`/student/exercises`)** | | | |
| View list of assigned exercises scoped to enrolled classes (`GET /api/v1/assignments`) | [x] | [x] | |
| Filter exercises by tab: In Progress / Active, Overdue, and Completed | [x] | [x] | |
| Filter exercises by subject (Math, Physics, Chemistry, etc.) and search by title | [x] | [x] | |
| View assignment briefing card: Teacher name, deadline (`due_at`), duration, question count | [x] | [x] | |
| View max allowed attempts vs. completed attempts count | [x] | [x] | |
| **4. Standalone Online Exam Taking Mode (`/student/exercises/:exerciseId/taking`)** | | | |
| Launch distraction-free fullscreen examination interface (`StudentExerciseTakingPage`) | [x] | [x] | |
| Anti-cheating & fullscreen enforcement modal warning | [x] | [x] | |
| Synchronized countdown timer with automatic exam submission upon time expiry | [x] | [x] | |
| Interactive question navigator palette with answered, unanswered, and flagged indicators | [x] | [x] | |
| Answer Part I questions: Multiple Choice single selection (A, B, C, D) | [x] | [x] | |
| Answer Part II questions: True/False evaluation for 4 distinct sub-items (a, b, c, d) | [x] | [x] | |
| Answer Part III questions: Short answer numerical value input | [x] | [x] | |
| On-screen virtual numpad helper for rapid and error-free numerical input in Part III | [x] | [x] | |
| Clear and responsive KaTeX rendering of mathematical equations and scientific notations | [x] | [x] | |
| Continuous LocalStorage auto-save mechanism protecting answers against accidental page reload or network drop | [x] | [x] | |
| Clear Answer / Reset selection button per question | [x] | [x] | |
| Review submission summary modal confirming answered vs. skipped questions before final submit | [x] | [x] | |
| Submit completed exam attempt to backend API (`PUT /api/v1/attempts/{id}/submit`) | [x] | [x] | |
| **5. Exam Results, Review & Score History** | | | |
| Instant display of preliminary score for objective questions (Part I & Part II) | [x] | [x] | |
| Total time taken calculation (`total_time_seconds`) and submission timestamp recording | [x] | [x] | |
| View detailed question-by-question review with correct answers & teacher feedback (when published) | [x] | [x] | |
| Personal historical scores and grade progress tracking over academic semesters | | | |
