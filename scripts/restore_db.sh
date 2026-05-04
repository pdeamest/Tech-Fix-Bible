#!/usr/bin/env bash
# scripts/restore_db.sh
# Restore a TechKB Postgres dump file into a target database.
#
# Usage:
#   TARGET_DB='postgresql://user:pass@host:port/db' \
#     ./scripts/restore_db.sh path/to/techkb-XXXXXXXX.dump
#
# WARNING: This DROPS all existing data in $TARGET_DB and replaces it.
# Use against a staging/local DB, NEVER against production without a
# fresh backup first.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: TARGET_DB='postgresql://...' $0 path/to/backup.dump"
  exit 1
fi

DUMPFILE="$1"

if [ ! -f "$DUMPFILE" ]; then
  echo "❌ Dump file not found: $DUMPFILE"
  exit 1
fi

if [ -z "${TARGET_DB:-}" ]; then
  echo "❌ TARGET_DB not exported."
  echo "   export TARGET_DB='postgresql://user:pass@host:port/db'"
  exit 1
fi

echo "→ Target DB: ${TARGET_DB:0:25}..."
echo "→ Dump file: $DUMPFILE"
echo ""
read -p "⚠️  This will DROP and REPLACE all data in target. Continue? [yes/NO] " confirm

if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo ""
echo "→ Restoring..."
pg_restore \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  --dbname="$TARGET_DB" \
  "$DUMPFILE"

echo ""
echo "✅ Restore complete."
echo ""
echo "→ Verify with:"
echo "   psql \"\$TARGET_DB\" -c 'SELECT COUNT(*) AS articles FROM knowledge_base;'"
