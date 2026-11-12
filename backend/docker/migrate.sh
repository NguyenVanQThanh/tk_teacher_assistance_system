#!/bin/sh
# File Name: migrate.sh
# Description: Apply Alembic migrations (also seeds sgk_docs via its migration).
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-12
# Updated By: AI Agent
set -eu

echo "migrate: running alembic upgrade head"
alembic upgrade head
