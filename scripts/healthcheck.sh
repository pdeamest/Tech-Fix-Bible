#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
#  scripts/healthcheck.sh
#  Smoke-tests the public API endpoints.
# ════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/healthcheck.sh                              # localhost
#   API_URL=https://your-api.railway.app ./healthcheck.sh # remote
# ════════════════════════════════════════════════════════════

set -euo pipefail

API="${API_URL:-http://localhost:8000}"
PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expected="${3:-200}"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [[ "$code" == "$expected" ]]; then
        echo "  ✓ $name ($code)"
        PASS=$((PASS+1))
    else
        echo "  ✗ $name — expected $expected, got $code"
        FAIL=$((FAIL+1))
    fi
}

echo "─── API health ──────────────────────────────────────────"
echo "Target: $API"
echo

check "health"                  "$API/api/health"
check "kb search (empty)"       "$API/api/kb/search"
check "kb search (query)"       "$API/api/kb/search?q=ospf"
check "error-code lookup"       "$API/api/kb/by-error-code/HTTP-401"
check "error-code case-insens." "$API/api/kb/by-error-code/http-401?exact=false"
check "error-code stats"        "$API/api/kb/error-codes/stats?limit=5"
check "academy list"            "$API/api/academy"
check "admin seed (no auth)"    "$API/api/admin/seed" 401

echo
echo "─── Summary ─────────────────────────────────────────────"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
