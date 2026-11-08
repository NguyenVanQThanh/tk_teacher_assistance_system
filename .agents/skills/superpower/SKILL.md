---
name: superpower
description: Core software engineering discipline and superpower workflows including TDD, systematic debugging, structured code review, and pre-completion verification.
---

<!--
File Name: SKILL.md
Description: Superpower engineering workflow and review discipline
Created At: 2026-11-07
Created By: Tam Khang
Updated At: 2026-11-07
Updated By: Tam Khang
-->

# Superpower Development & Review Methodology

This skill guides agents and subagents through structured engineering disciplines, ensuring that all planning, implementation, debugging, review, and verification follow rigorous standards.

## Core Disciplines

1. **Systematic Debugging & Root Cause Analysis**
   - Trace bugs to their underlying root cause before attempting code modifications.
   - Form hypotheses, inspect state, and reproduce issues consistently.
   - Reference: [systematic-debugging](../systematic-debugging/SKILL.md)

2. **Test-Driven Development (TDD)**
   - Follow strict Red-Green-Refactor cycles.
   - Write failing automated tests that reproduce defects or assert requirements before implementing changes.
   - Reference: [test-driven-development](../test-driven-development/SKILL.md)

3. **Rigorous Code Review & Static Analysis**
   - Audit code for security vulnerabilities, memory management, side effects, and architectural conformity.
   - Enforce soft-delete rules, English-only naming/comments, and strict `.env` / secret isolation.
   - Reference: [requesting-code-review](../requesting-code-review/SKILL.md) & [receiving-code-review](../receiving-code-review/SKILL.md)

4. **Verification Before Completion**
   - Never mark tasks as complete without running relevant automated test suites and verifying evidence.
   - Ensure all affected components continue functioning without regressions.
   - Reference: [verification-before-completion](../verification-before-completion/SKILL.md)

5. **Structured Planning & Subagent Delegation**
   - Decompose complex tasks into clear, atomic steps.
   - Dispatch focused subagents with explicit boundaries and responsibilities.
   - Reference: [writing-plans](../writing-plans/SKILL.md) & [executing-plans](../executing-plans/SKILL.md)

