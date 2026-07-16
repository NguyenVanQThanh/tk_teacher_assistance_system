# Coding Rules & Guidelines

This document outlines the core coding standards, architectural principles, and practices to be followed when developing in this repository.

## 1. File Structure & Header
Every code file (e.g., Python, SQL, JS, etc.) must begin with a standardized header block containing the following metadata:

```text
File Name: <name_of_the_file>
Description: <brief_description_of_the_file_purpose>
Created At: <YYYY-MM-DD>
Created By: <author_name_or_email>
Updated At: <YYYY-MM-DD>
Updated By: <author_name_or_email>
```

## 2. Comments & Documentation
- **Language**: All comments, docstrings, and in-code documentation MUST be written in **Standard English**.
- **User-Facing Language**: All text, labels, error messages, or descriptions displayed on the web interface or API responses for users to read MUST be written in **Vietnamese**.
- **Clarity**: Keep comments concise but descriptive enough to explain the *why* behind complex logic, not just the *what*.
- **Python**: Use PEP 257 standard for docstrings.
- **SQL**: Use `--` for inline comments or `/* ... */` for block comments, explaining complex queries or business logic.

## 3. Architecture
*(Specific architectural details used in this repo - update as needed)*
- **Pattern**: Follow the established architectural pattern (e.g., MVC, Clean Architecture, Microservices).
- **Separation of Concerns**: Keep business logic separate from framework-specific code or presentation layers.
- **Modularity**: Components should be loosely coupled and highly cohesive.

## 4. Techniques & Practices
*(Specific techniques used in this repo - update as needed)*
- **Version Control**: Follow standard Git Flow or trunk-based development. Use descriptive commit messages.
- **Error Handling**: Use structured exception handling. Do not silently swallow exceptions.
- **Testing**: Write unit tests for all core business logic.
- **Formatting**: Adhere to the designated linters and formatters (e.g., Black/Ruff for Python, Prettier for frontend).

## 5. Logging Guidelines
- **No Icons/Emojis**: Log messages must be clean text. **Do NOT use icons or emojis** in log statements to ensure log parsers and monitoring tools can process them efficiently without encoding issues.
- **Clarity**: Logs should be clear, structured, and provide enough context for debugging.

## 6. Security Restrictions
- **Strict Prohibition**: Under no circumstances should any script, tool, or automated process read, modify, or interact with `.env` files or any other files containing sensitive environment variables or secrets.
- **Secrets Management**: Rely on secure environment variable injection or a dedicated secrets manager instead of hardcoding or reading raw config files.
