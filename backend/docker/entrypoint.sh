#!/bin/sh
# File Name: entrypoint.sh
# Description: Backend container entrypoint. Runs migrate.sh, bootstrap_admin.sh, load_sgk.sh, then starts the app.
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-14
# Updated By: AI Agent
set -eu

DIR="$(dirname "$0")"
sh "$DIR/migrate.sh"
sh "$DIR/bootstrap_admin.sh"
sh "$DIR/load_sgk.sh"
exec "$@"
