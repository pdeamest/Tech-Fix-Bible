#!/usr/bin/env bash
# scripts/backup_db.sh
# Quick local backup of the Railway Postgres DB.
# Requires: DATABASE_PUBLIC_URL exported, pg_dump installed.

set -euo pipefail

if [ -z "${DATABASE_PUBLIC_URL:-}" ]; then
  echo "❌ DATABASE_PUBLIC_URL not exported"
  echo "   export DATABASE_PUBLIC_URL='postgresql://...'"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$REPO_ROOT/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUTFILE="$BACKUP_DIR/techkb-$TIMESTAMP.dump"

echo "→ Dumping to $OUTFILE ..."
pg_dump "$DATABASE_PUBLIC_URL" \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="$OUTFILE"

SIZE=$(du -h "$OUTFILE" | cut -f1)
echo "✅ Backup complete: $OUTFILE ($SIZE)"

# Show last 5 backups
echo ""
echo "→ Recent backups:"
ls -lht "$BACKUP_DIR" | head -6
