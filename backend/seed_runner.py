"""
KB Platform · Seed Runner (shared core)
---------------------------------------
Importable async functions used by BOTH:
  - seed.py           (CLI entry point)
  - admin.py          (FastAPI /api/admin/seed endpoint)

v3 changes:
  - ARTICLE_UPSERT now writes error_codes + scenario_type (migration 004).
  - Articles default to error_codes=[] and scenario_type=NULL if omitted,
    so older data files remain backward-compatible.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from seed_data import ARTICLES, ACADEMY, MANUFACTURERS, EXTRA_CERT_ENUM_VALUES

log = logging.getLogger("kb-platform.seed")


# ─────────────────────────────────────────────────────────────
#  Types
# ─────────────────────────────────────────────────────────────
class LogLine(TypedDict):
    ts: str
    level: str
    event: str
    message: str
    meta: dict[str, Any]


class SeedStats(TypedDict):
    inserted: int
    updated: int


class SeedResult(TypedDict):
    status: str
    duration_ms: int
    manufacturers: SeedStats
    knowledge_base: SeedStats
    academy_resources: SeedStats
    logs: list[LogLine]


# ─────────────────────────────────────────────────────────────
#  Log capture (dual sink)
# ─────────────────────────────────────────────────────────────
class LogCapture:
    def __init__(self) -> None:
        self.lines: list[LogLine] = []

    def _emit(self, level: str, event: str, message: str, **meta: Any) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        self.lines.append({
            "ts": ts, "level": level, "event": event,
            "message": message, "meta": meta,
        })
        kv = " ".join(f"{k}={_fmt(v)}" for k, v in meta.items())
        log_msg = f"{event:<26} {message}" + (f"  {kv}" if kv else "")
        getattr(log, level.lower(), log.info)(log_msg)

    def info(self, event: str, msg: str, **meta: Any) -> None:
        self._emit("INFO", event, msg, **meta)

    def debug(self, event: str, msg: str, **meta: Any) -> None:
        self._emit("DEBUG", event, msg, **meta)

    def warn(self, event: str, msg: str, **meta: Any) -> None:
        self._emit("WARN", event, msg, **meta)

    def error(self, event: str, msg: str, **meta: Any) -> None:
        self._emit("ERROR", event, msg, **meta)


def _fmt(v: Any) -> str:
    s = str(v)
    return f'"{s}"' if " " in s else s


# ─────────────────────────────────────────────────────────────
#  Schema preconditions
# ─────────────────────────────────────────────────────────────
async def ensure_schema_preconditions(engine) -> None:
    async with engine.begin() as conn:
        for value in EXTRA_CERT_ENUM_VALUES:
            await conn.execute(
                text(f"ALTER TYPE cert_name ADD VALUE IF NOT EXISTS '{value}'")
            )

    ddl = """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_kb_mfr_title') THEN
            ALTER TABLE knowledge_base
                ADD CONSTRAINT uq_kb_mfr_title UNIQUE (manufacturer_id, title);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_academy_cert_title') THEN
            ALTER TABLE academy_resources
                ADD CONSTRAINT uq_academy_cert_title UNIQUE (certification, title);
        END IF;
    END $$;
    """
    async with engine.begin() as conn:
        await conn.execute(text(ddl))


# ─────────────────────────────────────────────────────────────
#  Manufacturer upsert
# ─────────────────────────────────────────────────────────────
MANUFACTURER_UPSERT = text("""
    INSERT INTO manufacturers (slug, display_name, website_url)
    VALUES (:slug, :display_name, :website_url)
    ON CONFLICT (slug) DO UPDATE SET
        display_name = EXCLUDED.display_name,
        website_url  = EXCLUDED.website_url
    RETURNING id, (xmax = 0) AS inserted
""")


async def _seed_manufacturers(session: AsyncSession, cap: LogCapture, dry_run: bool) -> tuple[int, int]:
    inserted = updated = 0
    for m in MANUFACTURERS:
        if dry_run:
            cap.debug("seed.mfr.preview", m["display_name"], slug=m["slug"])
            continue
        result = await session.execute(MANUFACTURER_UPSERT, m)
        row = result.first()
        if row.inserted:
            inserted += 1
            cap.debug("seed.mfr.insert", m["display_name"], slug=m["slug"])
        else:
            updated += 1
    return inserted, updated


async def _load_manufacturer_map(session: AsyncSession, cap: LogCapture) -> dict[str, str]:
    result = await session.execute(text("SELECT slug, id FROM manufacturers"))
    mfr_map = {row.slug: str(row.id) for row in result.fetchall()}

    required = {a["manufacturer_slug"] for a in ARTICLES}
    missing = required - set(mfr_map.keys())
    if missing:
        cap.error("seed.precondition.fail",
                  "Missing manufacturers after upsert — this is a bug",
                  missing=sorted(missing))
        raise RuntimeError(f"Missing manufacturer slugs: {sorted(missing)}")

    cap.info("seed.manufacturers.loaded", f"{len(mfr_map)} manufacturers in map",
             count=len(mfr_map))
    return mfr_map


# ─────────────────────────────────────────────────────────────
#  Articles — now with error_codes + scenario_type (migration 004)
# ─────────────────────────────────────────────────────────────
ARTICLE_UPSERT = text("""
    INSERT INTO knowledge_base
        (manufacturer_id, title, description, source_url, tags,
         status, error_codes, scenario_type)
    VALUES
        (:mfr_id, :title, :description, :source_url, :tags,
         'unchecked', :error_codes, :scenario_type)
    ON CONFLICT (manufacturer_id, title) DO UPDATE SET
        description   = EXCLUDED.description,
        source_url    = EXCLUDED.source_url,
        tags          = EXCLUDED.tags,
        error_codes   = EXCLUDED.error_codes,
        scenario_type = EXCLUDED.scenario_type,
        updated_at    = NOW()
    RETURNING id, (xmax = 0) AS inserted
""")


def _normalize_error_codes(codes: list[str] | None) -> list[str]:
    """Uppercase + strip whitespace. Keeps matching consistent at query time."""
    if not codes:
        return []
    return [c.strip().upper() for c in codes if c and c.strip()]


async def _seed_articles(
    session: AsyncSession,
    mfr_map: dict[str, str],
    cap: LogCapture,
    dry_run: bool,
) -> tuple[int, int]:
    inserted = updated = 0
    for a in ARTICLES:
        error_codes = _normalize_error_codes(a.get("error_codes"))

        if dry_run:
            cap.debug("seed.kb.preview", a["title"][:70],
                      vendor=a["manufacturer_slug"],
                      codes=len(error_codes))
            continue

        result = await session.execute(ARTICLE_UPSERT, {
            "mfr_id":        mfr_map[a["manufacturer_slug"]],
            "title":         a["title"],
            "description":   a["description"],
            "source_url":    a["source_url"],
            "tags":          a["tags"],
            "error_codes":   error_codes,
            "scenario_type": a.get("scenario_type"),
        })
        row = result.first()
        if row.inserted:
            inserted += 1
            cap.debug("seed.kb.insert", a["title"][:70],
                      vendor=a["manufacturer_slug"],
                      scenario=a.get("scenario_type") or "-",
                      codes=len(error_codes))
        else:
            updated += 1
            cap.debug("seed.kb.update", a["title"][:70],
                      vendor=a["manufacturer_slug"],
                      scenario=a.get("scenario_type") or "-",
                      codes=len(error_codes))
    return inserted, updated


# ─────────────────────────────────────────────────────────────
#  Academy
# ─────────────────────────────────────────────────────────────
ACADEMY_UPSERT = text("""
    INSERT INTO academy_resources
        (certification, level, title, description, resource_url, is_free, tags, status)
    VALUES
        (:cert::cert_name, :level::cert_level, :title, :description,
         :resource_url, :is_free, :tags, 'unchecked')
    ON CONFLICT (certification, title) DO UPDATE SET
        level        = EXCLUDED.level,
        description  = EXCLUDED.description,
        resource_url = EXCLUDED.resource_url,
        is_free      = EXCLUDED.is_free,
        tags         = EXCLUDED.tags
    RETURNING id, (xmax = 0) AS inserted
""")


async def _seed_academy(session: AsyncSession, cap: LogCapture, dry_run: bool) -> tuple[int, int]:
    inserted = updated = 0
    for r in ACADEMY:
        if dry_run:
            cap.debug("seed.academy.preview", r["title"][:70], cert=r["certification"])
            continue

        result = await session.execute(ACADEMY_UPSERT, {
            "cert":         r["certification"],
            "level":        r["level"],
            "title":        r["title"],
            "description":  r["description"],
            "resource_url": r["resource_url"],
            "is_free":      r["is_free"],
            "tags":         r["tags"],
        })
        row = result.first()
        if row.inserted:
            inserted += 1
        else:
            updated += 1
    return inserted, updated


# ─────────────────────────────────────────────────────────────
#  Orchestration
# ─────────────────────────────────────────────────────────────
async def run_seed(
    session: AsyncSession,
    engine,
    *,
    dry_run: bool = False,
) -> SeedResult:
    cap = LogCapture()
    started = time.monotonic()

    total_codes = sum(len(a.get("error_codes") or []) for a in ARTICLES)
    cap.info("seed.start", "Seed run starting",
             dry_run=dry_run,
             manufacturers=len(MANUFACTURERS),
             articles=len(ARTICLES),
             academy=len(ACADEMY),
             total_error_codes=total_codes)

    if not dry_run:
        cap.info("seed.schema.ensure", "Ensuring enum values + unique constraints")
        await ensure_schema_preconditions(engine)

    mfr_ins, mfr_upd = await _seed_manufacturers(session, cap, dry_run)
    cap.info("seed.manufacturers.done", f"{mfr_ins} new, {mfr_upd} updated",
             inserted=mfr_ins, updated=mfr_upd)

    mfr_map = await _load_manufacturer_map(session, cap)

    kb_ins, kb_upd = await _seed_articles(session, mfr_map, cap, dry_run)
    ac_ins, ac_upd = await _seed_academy(session, cap, dry_run)

    if not dry_run:
        await session.commit()

    duration_ms = int((time.monotonic() - started) * 1000)

    cap.info(
        "seed.complete",
        f"mfr={mfr_ins}+{mfr_upd}, kb={kb_ins}+{kb_upd}, academy={ac_ins}+{ac_upd}",
        kb_inserted=kb_ins, kb_updated=kb_upd,
        academy_inserted=ac_ins, academy_updated=ac_upd,
        duration_ms=duration_ms,
    )

    return {
        "status":            "success",
        "duration_ms":       duration_ms,
        "manufacturers":     {"inserted": mfr_ins, "updated": mfr_upd},
        "knowledge_base":    {"inserted": kb_ins,  "updated": kb_upd},
        "academy_resources": {"inserted": ac_ins,  "updated": ac_upd},
        "logs":              cap.lines,
    }
