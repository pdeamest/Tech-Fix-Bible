"""
KB Platform · Seed CLI
----------------------
Thin wrapper around seed_runner.run_seed(). The actual logic lives in
seed_runner.py so it can be reused by the /api/admin/seed endpoint.

Usage:
    python seed.py                 # real seed
    python seed.py --dry-run       # preview, no writes
    python seed.py --verbose       # SQL echo + DEBUG logs
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from seed_runner import run_seed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("seed-cli")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    log.error("DATABASE_URL not set")
    sys.exit(1)


async def main(args: argparse.Namespace) -> int:
    engine = create_async_engine(DATABASE_URL, echo=args.verbose)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with SessionLocal() as session:
            result = await run_seed(session, engine, dry_run=args.dry_run)

        log.info("─" * 60)
        log.info("Result: %s", result["status"])
        log.info("  duration       : %d ms", result["duration_ms"])
        log.info("  knowledge_base : %2d inserted, %2d updated",
                 result["knowledge_base"]["inserted"],
                 result["knowledge_base"]["updated"])
        log.info("  academy        : %2d inserted, %2d updated",
                 result["academy_resources"]["inserted"],
                 result["academy_resources"]["updated"])
        log.info("─" * 60)
        return 0
    except Exception:
        log.exception("Seed failed")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the KB Platform database.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    ns = parser.parse_args()

    if ns.verbose:
        logging.getLogger("kb-platform.seed").setLevel(logging.DEBUG)

    sys.exit(asyncio.run(main(ns)))
