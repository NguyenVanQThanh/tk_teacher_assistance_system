# Feature Completion & Memory Rules

This document outlines the workflow and requirements for the AI Agent when completing a feature or fixing a business issue.

## 1. User Confirmation
- When the agent finishes implementing a feature or fixing a bug, **it MUST ask the user for confirmation** to ensure the task is fully completed before finalizing.

## 2. Memory File Creation
- Once the user confirms completion, the agent MUST generate a markdown memory file inside the `.claude/memory/` directory.
- The file MUST be placed in an appropriate subfolder such as `.claude/memory/feature/` or `.claude/memory/fix/`.
- The file should follow a descriptive naming convention (e.g., `feature_login_module.md` or `bugfix_user_auth.md`).

## 3. Required File Structure
Every memory file MUST include the metadata header and the structured sections below. The primary goal of this file is to provide complete context for future tasks and reference.

```text
File Name: <name_of_the_file>
Created At: <YYYY-MM-DD>
Created By: AI Agent / <author>
Updated At: <YYYY-MM-DD>
Updated By: AI Agent / <author>
```

### Summary
A high-level summary of what was accomplished in this feature or fix.

### Feature Specifications
- Detailed description of the specifications and business logic implemented in the new feature.
- List out any specific behaviors or edge cases that were addressed.

### Bug & Feature Context
- If this was a bug fix, clearly state what the bug was.
- Document which feature the bug was related to, how it manifested, and its root cause.

### Solution & Technical Details
- Explain the solution implemented.
- List the specific technologies, architectural patterns, algorithms, or techniques used to solve the problem.
- Include important file paths that were modified or created.

## 4. Purpose
The detailed documentation within the memory file must be written clearly with the explicit purpose of **providing full context for the next implementation phase or future bug fixes**. Any future agent reading this memory file should be able to instantly understand the business logic, what changed, and how it was resolved.
