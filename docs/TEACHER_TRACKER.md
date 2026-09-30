<!--
File Name: TEACHER_TRACKER.md
Description: Comprehensive tracker for Teacher and Homeroom Teacher role use cases across Backend, Frontend, and Testing.
Created At: 2026-09-30
Created By: Tam Khang
Updated At: 2026-09-30
Updated By: Tam Khang
-->

# Teacher Role Use Cases Tracker

> Path: `docs/TEACHER_TRACKER.md` · Role: **Teacher (Giáo viên Bộ môn & Giáo viên Chủ nhiệm)**  
> Created By: `Tam Khang` · Updated By: `Tam Khang` · Updated At: `2026-09-30`  
> Scope: Teaching materials, exercise bank, AI exam extraction, grading, schedules, student assessment, and dedicated homeroom class management.

| Use Case | BE | FE | Test |
| :--- | :---: | :---: | :---: |
| **1. Authentication & Profile** | | | |
| Teacher login with phone/email and password (`POST /api/v1/auth/login`) | [x] | [x] | |
| View teacher personal profile and assigned teaching subjects (`GET /api/v1/auth/me`) | [x] | [x] | |
| Update teacher profile info and avatar (`/teacher/profile`) | [x] | [x] | |
| Change teacher account password (`POST /api/v1/auth/change-password`) | [x] | [x] | |
| Secure session logout and token invalidation (`POST /api/v1/auth/logout`) | [x] | [x] | |
| **2. Subject Teacher Dashboard (`/teacher`)** | | | |
| Grade distribution breakdown (phổ điểm) per assigned class and exercise | [x] | | |
| Class competency spider / radar chart across knowledge domains | | | |
| Frequently missed question types and error pattern diagnostics | | | |
| Real-time submission timeline and last-minute submission warning flags | | | |
| Quick actions: Create exercise, assign homework, upload document | [x] | [x] | |
| **3. Document & Learning Material Repository (`/teacher/documents`)** | | | |
| Browse shared and personal teaching documents (`GET /api/v1/documents`) | [x] | [x] | |
| Filter documents by subject, grade level, and file format | [x] | [x] | |
| Upload documents with title, subject, grade, and description (`POST /api/v1/documents/upload`) | [x] | [x] | |
| Download teaching document securely (`GET /api/v1/documents/{id}/download`) | [x] | [x] | |
| Soft delete document with status `DELETED` (`DELETE /api/v1/documents/{id}`) | [x] | [x] | |
| Restore soft-deleted document (`POST /api/v1/documents/{id}/restore`) | [x] | [x] | |
| Document repository dashboard metrics: total files, storage used (`GET /api/v1/documents/dashboard`) | [x] | [x] | |
| **4. Exercise & Question Bank (`/teacher/exercises`)** | | | |
| Browse exercise bank with keyset cursor pagination and multi-filters (`GET /api/v1/exercises`) | [x] | [x] | |
| Filter exercises by subject, grade (10, 11, 12), difficulty, and status | [x] | [x] | |
| View exercise details and question list preview (`GET /api/v1/exercises/{id}`) | [x] | [x] | |
| Create exercise manually with title, subject, duration, and instructions (`POST /api/v1/exercises`) | [x] | [x] | |
| Formulate Part I questions: Multiple Choice 4 options ABCD with correct key (`POST /api/v1/questions`) | [x] | [x] | |
| Formulate Part II questions: True/False 4 sub-items a-b-c-d with independent keys | [x] | [x] | |
| Formulate Part III questions: Short answer / numerical entry | [x] | [x] | |
| Math LaTeX formula typing with real-time KaTeX visual preview | [x] | [x] | |
| Tag questions with cognitive levels: Recognition, Understanding, Application | [x] | [x] | |
| Bulk import questions from standardized DOCX / PDF template (`POST /api/v1/questions/import`) | [x] | [x] | |
| AI Gemini Multimodal Vision OCR extraction: Upload PDF/Image exam for auto-parsing | [x] | [x] | |
| Interactive preview & inline editing of OCR-extracted questions and LaTeX formulas | [x] | [x] | |
| Export formatted exam paper to official MoET layout PDF | [x] | [x] | |
| Soft delete exercise (`DELETE /api/v1/exercises/{id}`) | [x] | [x] | |
| **5. Class Homework & Exam Assignments** | | | |
| Assign exercise to one or more teaching classes (`POST /api/v1/assignments`) | [x] | [x] | |
| Configure assignment parameters: due date (`due_at`), time limit, max attempts | [x] | [x] | |
| RBAC Data Scoping: Restrict assignment dispatch exclusively to teacher's assigned classes | [x] | [x] | |
| Track class assignment submission progress and completion rate | [x] | [x] | |
| Cancel or soft delete class assignment | [x] | [x] | |
| **6. Grading & Student Attempt Evaluation (`/teacher/grading`)** | | | |
| View submitted student attempts list filtered by class, exercise, and grading status | [x] | [x] | |
| Automatic objective grading for Part I (MCQ) and Part II (True/False) | [x] | [x] | |
| Manual grading interface for Part III numerical / short answer questions | [x] | [x] | |
| Teacher feedback commentary input per question and overall attempt | [x] | [x] | |
| 3-state grading lifecycle workflow: `pending_grading` -> `pending_review` -> `approved` | [x] | [x] | |
| Publish finalized grades to students upon approval | [x] | [x] | |
| Export grading sheet and student scores to Excel | | | |
| **7. Teaching Classes & Student Tracking (`/teacher/classes`)** | | | |
| View list of classes assigned to teacher (`GET /api/v1/classes`) | [x] | [x] | |
| View class detail view with enrolled student roster (`/teacher/classes/:classId`) | [x] | [x] | |
| View student academic submission history within class | [x] | [x] | |
| Monitor student study engagement and detect students cramming or missing deadlines | | | |
| **8. Teaching Schedule (`/teacher/schedule`)** | | | |
| Weekly teaching timetable with assigned time periods and class rooms | | | |
| Daily agenda view with upcoming class sessions | | | |
| Filter schedule by semester and academic week | | | |
| **9. Homeroom Teacher Dedicated Use Cases (`/teacher/homeroom`)** | | | |
| View assigned homeroom class overview: total headcount, gender ratio, class officers | [x] | [x] | |
| Homeroom student roster directory with complete student profile information | [x] | [x] | |
| Parent & guardian contact information access (parent phone numbers, home address) | | | |
| Class-wide attendance & study diligence tracking dashboard | | | |
| Multi-subject overall academic standing & cumulative GPA monitoring | | | |
| Comprehensive gradebook matrix across all enrolled subjects for homeroom students | | | |
| Early warning & intervention alert system for at-risk homeroom students (falling grades, chronic late submissions) | | | |
| Compose and broadcast announcements / SMS notifications to homeroom students and parents | | | |
| Log behavioral notes and conduct evaluation per homeroom student | | | |
| Export homeroom semester summary report and student conduct evaluations to Excel / PDF | | | |
