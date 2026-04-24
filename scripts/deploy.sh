#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
#  scripts/deploy.sh
#  Runs migrations in order, then seeds the database.
#  Idempotent — safe to re-run.
# ════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/deploy.sh              # apply + seed
#   ./scripts/deploy.sh --dry-run    # seed in dry-run mode
#   ./scripts/deploy.sh --skip-seed  # migrations only
#
# Requires DATABASE_URL env var (postgresql://... or postgres://...)
# ════════════════════════════════════════════════════════════

set -euo pipefail

DRY_RUN=""
SKIP_SEED=""
for arg in "$@"; do
    case $arg in
        --dry-run)    DRY_RUN="--dry-run" ;;
        --skip-seed)  SKIP_SEED="1" ;;
    esac
done

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# psql needs the sync URL, not the asyncpg one
PSQL_URL="${DATABASE_URL/postgresql+asyncpg:\/\//postgresql://}"

echo "─── Migrations ──────────────────────────────────────────"
for migration in database/schema.sql \
                 database/003_is_admin_and_manufacturers.sql \
                 database/004_error_codes.sql; do
    if [[ -f "$migration" ]]; then
        echo "  → $migration"
        psql "$PSQL_URL" -v ON_ERROR_STOP=1 -f "$migration" > /dev/null
    else
        echo "  ! skipped (not found): $migration"
    fi
done

if [[ -n "$SKIP_SEED" ]]; then
    echo "─── Seed skipped (--skip-seed) ──────────────────────────"
    exit 0
fi

echo "─── Seed ────────────────────────────────────────────────"
cd backend
python seed.py $DRY_RUN
cd ..

echo "─── Done ────────────────────────────────────────────────"
