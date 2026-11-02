#!/usr/bin/env bash
# Dumps the PostgreSQL database of the compose stack to backups/prumo-YYYYMMDD-HHMM.sql.gz.
# Usage: deploy/backup.sh            (production stack, docker-compose.yml)
#        COMPOSE_FILE=docker-compose.dev.yml deploy/backup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

compose_file="${COMPOSE_FILE:-docker-compose.yml}"
mkdir -p backups
target="backups/prumo-$(date +%Y%m%d-%H%M).sql.gz"
tmp="${target}.partial"

docker compose -f "$compose_file" exec -T db sh -c \
  'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --clean --if-exists --no-owner --no-privileges' \
  | gzip -9 > "$tmp"
mv "$tmp" "$target"
echo "$target"
