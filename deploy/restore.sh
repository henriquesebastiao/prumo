#!/usr/bin/env bash
# Restores a backup made by backup.sh, replacing the current database and, when the matching
# ...-uploads.tar.gz exists next to it, the uploads volume (covers).
# Usage: deploy/restore.sh backups/prumo-20261117-1430.sql.gz
#        PRUMO_RESTORE_CONFIRM=yes deploy/restore.sh <file>   (no prompt)
set -euo pipefail
cd "$(dirname "$0")/.."

file="${1:-}"
if [[ -z "$file" || ! -f "$file" ]]; then
  echo "Uso: deploy/restore.sh <arquivo .sql.gz>" >&2
  exit 1
fi
compose_file="${COMPOSE_FILE:-docker-compose.yml}"

if [[ "${PRUMO_RESTORE_CONFIRM:-}" != "yes" ]]; then
  echo "Isto substitui TODOS os dados do banco atual pelo conteúdo de $file."
  read -r -p "Digite 'restaurar' para continuar: " answer
  [[ "$answer" == "restaurar" ]] || { echo "Cancelado."; exit 1; }
fi

has_api=false
if docker compose -f "$compose_file" ps --services --status running 2>/dev/null | grep -qx api; then
  has_api=true
  docker compose -f "$compose_file" stop api
fi

gunzip -c "$file" | docker compose -f "$compose_file" exec -T db sh -c \
  'psql --quiet --set ON_ERROR_STOP=1 --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' > /dev/null

uploads="${file%.sql.gz}-uploads.tar.gz"
if [[ -f "$uploads" ]] && docker compose -f "$compose_file" config --services | grep -qx api; then
  docker compose -f "$compose_file" run --rm --no-deps -T --entrypoint sh api \
    -c 'find /data/uploads -mindepth 1 -delete && tar -C /data/uploads -xzf -' < "$uploads"
  echo "Arquivos restaurados de $uploads."
fi

if [[ "$has_api" == true ]]; then
  docker compose -f "$compose_file" start api
fi
echo "Banco restaurado de $file."
