#!/bin/sh
# File Name: bootstrap_admin.sh
# Description: Ensure the primary Admin account exists on a freshly migrated database.
# Created At: 2026-11-14
# Created By: AI Agent
# Updated At: 2026-11-14
# Updated By: AI Agent
#
# Runs after migrate.sh (tables must exist) and before load_sgk.sh (so the admin can
# log in while the 2.1 GB SGK restore is still running).
#
# Inputs (from deploy/.env.prod or the container environment):
#   ADMIN_PHONE           login identifier — REQUIRED to create the account
#   ADMIN_PASSWORD        plain password, bcrypt-hashed before storage
#   ADMIN_EMAIL           optional metadata (email login is not supported)
#   ADMIN_FULL_NAME       optional, defaults to "System Administrator"
#   ADMIN_RESET_PASSWORD  optional, "1" forces the password back to ADMIN_PASSWORD
#
# With neither ADMIN_PHONE nor ADMIN_PASSWORD set the script exits 0 and creates
# nothing, so dev/CI containers start unchanged. A half-filled or unsafe config
# exits non-zero on purpose: the deploy then fails loudly instead of leaving a
# production database nobody can log into.
set -eu

echo "bootstrap_admin: checking primary admin account"
python /app/app/scripts/bootstrap_admin.py
