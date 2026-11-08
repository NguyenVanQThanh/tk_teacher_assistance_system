---
name: receiving-code-review
description: Handle review feedback rigorously — verify each point technically before accepting or pushing back.
license: MIT
user-invocable: true
allowed-tools: [read_file, write_file, edit, bash, grep, todo, ask_user_question]
---

<!-- File Name: SKILL.md
Description: Receiving-code-review skill (superpowers, improved for Vibe)
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# Receiving Code Review

Process review feedback without ego and without blind acceptance.

## For each finding

1. Read the reviewer's reasoning and the referenced code yourself.
2. Classify: VALID (fix it), INVALID (push back with a technical explanation
   and evidence), or QUESTION (ask the user when it changes behavior/spec).
3. For VALID findings: implement the fix, keep repo rules (English, `Tam Khang`
   header, soft delete, no `.env`), and re-run the relevant verification.
4. Do not batch unrelated refactors into a fix; keep diffs reviewable.
5. Reply to each comment with what was done (or why not). Re-request review
   (`requesting-code-review`) after blocker/major fixes.
