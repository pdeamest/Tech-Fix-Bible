"""
KB Platform · Admin Router  (v2 — hardened)
-------------------------------------------
Changes vs v1:
  1. require_admin() now reads users.is_admin from the database (not env).
     ADMIN_EMAILS env var is still read — but only by main.py's OAuth
     callback as a BOOTSTRAP mechanism (promote on first login).
     Revocation is DB-only:  UPDATE users SET is_admin = FALSE WHERE ...

  2. Every admin action is persisted to audit_log AND emitted to stdout in
     Splunk-parseable key=value format. This satisfies two requirements
     simultaneously: live console monitoring + durable audit trail.

Endpoints:
  POST /api/admin/seed           Trigger DB seed (idempotent upsert)
  POST /api/admin/health-check   Trigger link health check (background)
  GET  /api/admin/audit          Last N admin actions (admin-only)
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import shared pieces from main.py — NOT duplicated
from main import (
    engine,
    get_current_user,
    get_db,
    run_link_health_check,
)
from seed_runner import run_seed

log = logging.getLogger("kb-platform.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─────────────────────────────────────────────────────────────
#  Admin gate  (DB-backed)
# ─────────────────────────────────────────────────────────────
async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Authorization dep: JWT-authenticated AND users.is_admin = TRUE.

    current_user already comes from main.get_current_user which (post-v2)
    SELECTs is_admin. If the column is FALSE we reject — no env-var fallback,
    no implicit privilege. See module docstring for the bootstrap path.
    """
    if not current_user.get("is_admin"):
        log.warning(
            "admin.forbidden user_id=%s email=%s",
            current_user.get("id"), current_user.get("email"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ─────────────────────────────────────────────────────────────
#  Audit logger
# ─────────────────────────────────────────────────────────────
async def log_admin_action(
    db: AsyncSession,
    *,
    admin: dict,
    action: str,
    target_table: str = "system",
    target_id: Optional[str] = None,
    diff: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
    commit: bool = True,
) -> None:
    """
    Dual-write audit record:
      1. INSERT INTO audit_log       (durable)
      2. Emit to stdout              (container logs, Splunk-friendly)

    The stdout line is deliberately phrased per user requirement:
      "Admin [Email] disparó el proceso de Seeding en [Timestamp]"

    The structured key=value metadata that follows makes it trivially
    indexable by any log aggregator.
    """
    ts = datetime.now(timezone.utc).isoformat()
    client_ip = request.client.host if request and request.client else None

    diff_with_meta: dict[str, Any] = {
        **(diff or {}),
        "client_ip": client_ip,
        "ts_utc": ts,
    }

    await db.execute(
        text("""
            INSERT INTO audit_log (table_name, record_id, action, changed_by, diff)
            VALUES (:table, :record_id, :action, :changed_by, :diff::jsonb)
        """),
        {
            "table":       target_table,
            "record_id":   target_id or str(admin["id"]),
            "action":      action,
            "changed_by":  str(admin["id"]),
            "diff":        _json_dumps(diff_with_meta),
        },
    )
    if commit:
        await db.commit()

    # Human-readable phrase first, then machine-parseable kv pairs.
    action_phrase = _friendly_phrase(action)
    log.info(
        "Admin [%s] %s en [%s]  audit.action=%s user_id=%s client_ip=%s target=%s",
        admin["email"], action_phrase, ts,
        action, admin["id"], client_ip or "-", target_table,
    )


def _friendly_phrase(action: str) -> str:
    return {
        "seed.trigger":        "disparó el proceso de Seeding",
        "seed.dry_run":        "disparó un Dry-Run de Seeding",
        "healthcheck.trigger": "disparó un Link Health Check",
        "audit.read":          "consultó el audit log",
    }.get(action, f"ejecutó la acción '{action}'")


def _json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj, default=str, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────
#  POST /api/admin/seed
# ─────────────────────────────────────────────────────────────
@router.post("/seed", status_code=status.HTTP_200_OK)
async def trigger_seed(
    request: Request,
    dry_run: bool = Query(default=False),
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Idempotent DB seed. Uses ON CONFLICT DO UPDATE on natural keys, safe to
    re-run. Response contains structured stats + log lines for UI display.
    """
    started = time.monotonic()

    # Audit FIRST, so even a failing seed leaves a trace
    await log_admin_action(
        db,
        admin=admin,
        action="seed.dry_run" if dry_run else "seed.trigger",
        target_table="knowledge_base",
        diff={"dry_run": dry_run, "trigger": "api"},
        request=request,
        commit=True,
    )

    try:
        result = await run_seed(db, engine, dry_run=dry_run)
        log.info(
            "admin.seed.ok user=%s dry_run=%s duration_ms=%d "
            "kb_inserted=%d kb_updated=%d academy_inserted=%d academy_updated=%d",
            admin["email"], dry_run, result["duration_ms"],
            result["knowledge_base"]["inserted"],
            result["knowledge_base"]["updated"],
            result["academy_resources"]["inserted"],
            result["academy_resources"]["updated"],
        )
        return result

    except Exception as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        log.exception("admin.seed.failed user=%s elapsed_ms=%d",
                      admin["email"], elapsed)
        # Best-effort failure audit
        try:
            await log_admin_action(
                db, admin=admin,
                action="seed.failed",
                diff={"error": str(exc), "dry_run": dry_run},
                request=request, commit=True,
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seed failed: {exc}",
        )


# ─────────────────────────────────────────────────────────────
#  POST /api/admin/health-check
# ─────────────────────────────────────────────────────────────
@router.post("/health-check", status_code=status.HTTP_202_ACCEPTED)
async def trigger_health_check(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Kicks off link health check in background; returns 202 immediately."""
    await log_admin_action(
        db, admin=admin, action="healthcheck.trigger",
        target_table="knowledge_base", request=request, commit=True,
    )

    async def _job() -> None:
        try:
            await run_link_health_check()
        except Exception:
            log.exception("admin.healthcheck.failed")

    asyncio.create_task(_job())
    return {"message": "Health check started in background"}


# ─────────────────────────────────────────────────────────────
#  GET /api/admin/audit
# ─────────────────────────────────────────────────────────────
@router.get("/audit")
async def read_audit_log(
    limit: int = Query(default=50, ge=1, le=500),
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Recent admin actions, joined with user email for display."""
    result = await db.execute(
        text("""
            SELECT
                a.id, a.table_name, a.action, a.diff,
                a.created_at, u.email AS admin_email
            FROM   audit_log a
            LEFT JOIN users u ON u.id = a.changed_by
            ORDER BY a.created_at DESC
            LIMIT  :limit
        """),
        {"limit": limit},
    )
    return [dict(r) for r in result.mappings().all()]
