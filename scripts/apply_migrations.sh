#!/usr/bin/env bash
# scripts/apply_migrations.sh
# Apply all pending DB migrations to Tech-Fix-Bible Postgres in Railway.
# Requires: DATABASE_PUBLIC_URL exported, psql installed.

set -euo pipefail

if [ -z "${DATABASE_PUBLIC_URL:-}" ]; then
  echo "❌ DATABASE_PUBLIC_URL not exported. Run: export DATABASE_PUBLIC_URL='...'"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIGRATIONS_DIR="$REPO_ROOT/database"

if [ ! -d "$MIGRATIONS_DIR" ]; then
  echo "❌ Migrations directory not found: $MIGRATIONS_DIR"
  exit 1
fi

echo "→ DATABASE_PUBLIC_URL len=${#DATABASE_PUBLIC_URL} prefix=${DATABASE_PUBLIC_URL:0:25}"

echo "→ Testing connection..."
psql "$DATABASE_PUBLIC_URL" -c "SELECT version();" -A -t \
  || { echo "❌ Connection failed"; exit 1; }
echo "✓ Connection OK"

echo ""
echo "→ Tables before migrations:"
psql "$DATABASE_PUBLIC_URL" -c "\dt"

MIGRATIONS=(
  "001_initial_schema.sql"
  "003_is_admin_and_manufacturers.sql"
  "004_error_codes.sql"
  "005_karma_trigger_hotfix.sql"
  "006_certifications_table.sql"
)

for f in "${MIGRATIONS[@]}"; do
  FULL="$MIGRATIONS_DIR/$f"
  if [ ! -f "$FULL" ]; then
    echo "❌ Migration file missing: $FULL"
    exit 1
  fi
  echo ""
  echo "→ Applying $f ..."
  PGOPTIONS='-c client_min_messages=warning' \
    psql "$DATABASE_PUBLIC_URL" -v ON_ERROR_STOP=1 -f "$FULL"
  echo "✓ $f applied"
done

echo ""
echo "→ Tables after migrations:"
psql "$DATABASE_PUBLIC_URL" -c "\dt"

echo ""
echo "✅ All migrations applied successfully"
