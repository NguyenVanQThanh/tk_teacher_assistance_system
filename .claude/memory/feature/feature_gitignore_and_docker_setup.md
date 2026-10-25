File Name: feature_gitignore_and_docker_setup.md
Created At: 2026-07-10
Created By: AI Agent / Antigravity
Updated At: 2026-07-10
Updated By: AI Agent / Antigravity

### Summary
Configured a standard `.gitignore` file for the Python/FastAPI project, removed the `.env` file (containing sensitive configurations) from the git history of the last two commits, and assisted in setting up the local execution environment using Docker and Alembic.

### Feature Specifications
- **.gitignore**: Ignores redundant files such as Python cache (`__pycache__/`, `.pyc`), virtual environments (`.venv/`), IDE configurations (`.vscode/`, `.idea/`), OS-specific files (`.DS_Store`), and sensitive environment files (`.env`, `.env.*.local`) while keeping `.env.example`.
- **Git History Refactor**: Removed the `.env` file from the tracking history of the last two commits to prevent sensitive credential leaks to the remote repository, followed by a successful force push.
- **Local Environment Bootstrap**: Created the `requirements.txt` file, started PostgreSQL via Docker Compose, ran migrations, and seeded baseline data.

### Bug & Feature Context
- The `.env` file was accidentally tracked by Git in the last two commits.
- The initial `docker compose up -d` failed with a port binding issue on port `5432` because a previous network resource or container was not cleanly removed.
- The `alembic` command was not recognized initially because the Python virtual environment had not been created and activated.

### Solution & Technical Details
- **Virtual Environment & Dependencies**: Created a virtual environment using `py -m venv .venv` and installed core packages via [requirements.txt](file:///e:/tk_teacher_assistance_system/requirements.txt).
- **Git History Rewrite**:
  1. Checked out the parent commit `1703425`.
  2. Cherry-picked the first commit (`8593802`), ran `git rm --cached .env`, and amended the commit.
  3. Cherry-picked the second commit (`ffd499a`), resolved the modify/delete conflict on `.env` by discarding the file, and committed the remaining changes.
  4. Updated the local branch pointer `TK/sprint_0` to the new HEAD and performed `git push -f origin TK/sprint_0`.
- **Docker & DB Initialization**:
  1. Ran `docker compose down` to clear network resources, followed by `docker compose up -d` to restart PostgreSQL with successful port mapping on port `5432`.
  2. Activated the `.venv` virtual environment and executed `alembic upgrade head` to run migration scripts and initialize tables.
  3. Executed `python seed.py` to seed sample system roles (`Admin`, `Teacher`, `Student`) into the `roles` table.
