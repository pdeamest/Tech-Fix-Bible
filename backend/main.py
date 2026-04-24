"""
KB Platform · FastAPI Backend
-----------------------------
Run: uvicorn main:app --reload --port 8000

v3 changes (iteration: GIN search engine + analytics):
  - get_current_user now reads users.is_admin (migration 003)
  - OAuth callback bootstraps admins via ADMIN_EMAILS env (promote-only)
  - KBArticleOut exposes error_codes[] and scenario_type (migration 004)
  - /api/kb/search SELECT extended with error_codes + scenario_type
  - /api/kb/{id} SELECT extended with error_codes + scenario_type
  - NEW: GET /api/kb/by-error-code/{code}     (GIN-indexed lookup)
  - NEW: GET /api/kb/error-codes/stats        (unnest + GROUP BY top N)
  - /api/admin/health-check moved to admin.py (shared require_admin gate)
  - app.include_router(admin_router) wires the admin namespace
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Literal, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from pydantic import UUID4, BaseModel, HttpUrl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.middleware.sessions import SessionMiddleware

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
DATABASE_URL   = os.environ["DATABASE_URL"]          # postgresql+asyncpg://user:pass@host/db
SECRET_KEY     = os.environ["SECRET_KEY"]            # openssl rand -hex 32
ALGORITHM      = "HS256"
TOKEN_EXPIRE   = 60 * 24 * 7                         # minutes → 7 days
FRONTEND_URL   = os.environ.get("FRONTEND_URL", "http://localhost:3000")
HEALTH_CHECK_INTERVAL_HOURS = int(os.environ.get("HEALTH_CHECK_HOURS", "6"))

# Admin bootstrap allowlist (promote-only, see OAuth callback below)
ADMIN_EMAIL_BOOTSTRAP: set[str] = {
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "").split(",")
    if e.strip()
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kb-platform")

if ADMIN_EMAIL_BOOTSTRAP:
    logger.info("admin.bootstrap.configured emails=%d", len(ADMIN_EMAIL_BOOTSTRAP))

# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# ─────────────────────────────────────────────
#  JWT helpers
# ─────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """
    JWT-authenticated user lookup. Includes is_admin (migration 003) so
    the admin router can gate without re-hitting the DB.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    payload = decode_token(auth_header.split(" ", 1)[1])
    user_id = payload.get("sub")

    result = await db.execute(
        text("""
            SELECT id, email, display_name, karma_score, is_admin
            FROM users
            WHERE id = :id AND is_active = TRUE
        """),
        {"id": user_id},
    )
    user = result.mappings().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return dict(user)


# ─────────────────────────────────────────────
#  Google OAuth2
# ─────────────────────────────────────────────
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# ─────────────────────────────────────────────
#  Async Link Health Checker
# ─────────────────────────────────────────────
async def check_single_url(url: str, timeout: int = 10) -> Literal["online", "broken"]:
    """Performs a HEAD request; falls back to GET on 405."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.head(url)
            if resp.status_code == 405:
                resp = await client.get(url)
            return "online" if resp.status_code < 400 else "broken"
    except Exception:
        return "broken"


async def run_link_health_check(db: AsyncSession) -> None:
    """Checks all KB articles and Academy resources; updates status in DB."""
    logger.info("Starting link health check …")

    for table, url_col in (("knowledge_base", "source_url"),
                           ("academy_resources", "resource_url")):
        result = await db.execute(text(f"SELECT id, {url_col} AS url FROM {table}"))  # noqa: S608
        rows = result.fetchall()

        tasks = [check_single_url(row.url) for row in rows]
        statuses = await asyncio.gather(*tasks, return_exceptions=True)

        for row, link_status in zip(rows, statuses):
            new_status = link_status if isinstance(link_status, str) else "broken"
            await db.execute(
                text(
                    f"UPDATE {table} "  # noqa: S608
                    f"SET status = :s, last_health_check = NOW() "
                    f"WHERE id = :id"
                ),
                {"s": new_status, "id": str(row.id)},
            )

    await db.commit()
    logger.info("Link health check complete.")


# ─────────────────────────────────────────────
#  Scheduler
# ─────────────────────────────────────────────
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        scheduler.add_job(
            run_link_health_check,
            "interval",
            hours=HEALTH_CHECK_INTERVAL_HOURS,
            args=[session],
            next_run_time=datetime.now(),
        )
    scheduler.start()
    yield
    scheduler.shutdown()


# ─────────────────────────────────────────────
#  FastAPI App
# ─────────────────────────────────────────────
app = FastAPI(
    title="Tech-Fix-Bible API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
#  Pydantic Schemas
# ─────────────────────────────────────────────
class KBArticleOut(BaseModel):
    id: UUID4
    manufacturer_id: UUID4
    manufacturer_name: str
    title: str
    description: str
    source_url: HttpUrl
    tags: list[str]
    status: str
    error_codes: list[str]          # migration 004
    scenario_type: Optional[str]    # migration 004
    resolution_score: Optional[float]
    total_votes: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class VoteIn(BaseModel):
    kb_id: UUID4
    vote: Literal["like", "dislike"]


class AcademyResourceOut(BaseModel):
    id: UUID4
    certification: str
    level: str
    title: str
    description: str
    resource_url: HttpUrl
    status: str
    tags: list[str]
    is_free: bool


class UserOut(BaseModel):
    id: UUID4
    email: str
    display_name: str
    karma_score: int
    is_admin: bool


class ErrorCodeStat(BaseModel):
    """One row in the Top N error-code ranking."""
    code:              str
    frequency:         int
    vendors:           list[str]
    sample_article_id: Optional[UUID4]


class ErrorCodeStatsResponse(BaseModel):
    total_unique_codes:  int
    total_code_uses:     int
    articles_with_codes: int
    top:                 list[ErrorCodeStat]


# ─────────────────────────────────────────────
#  Routes · Health
# ─────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ─────────────────────────────────────────────
#  Routes · Google OAuth2
# ─────────────────────────────────────────────
@app.get("/api/auth/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/api/auth/callback", name="google_callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    OAuth callback with admin bootstrap:
      - If user's email is in ADMIN_EMAILS env, is_admin is promoted to TRUE
        on first login (or preserved if already TRUE).
      - Env can PROMOTE only — removal does not revoke. Use the revoke
        endpoint or direct SQL to degrade.
    """
    try:
        token_data = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    user_info = token_data.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not retrieve user info from Google")

    google_sub = user_info["sub"]
    email      = user_info["email"]
    name       = user_info.get("name", email.split("@")[0])
    avatar     = user_info.get("picture")

    is_bootstrap_admin = email.lower() in ADMIN_EMAIL_BOOTSTRAP

    result = await db.execute(
        text("""
            INSERT INTO users (google_sub, email, display_name, avatar_url, is_admin, last_login_at)
            VALUES (:sub, :email, :name, :avatar, :is_admin, NOW())
            ON CONFLICT (google_sub) DO UPDATE
                SET last_login_at = NOW(),
                    avatar_url    = EXCLUDED.avatar_url,
                    -- Env can PROMOTE, never demote. Keep existing TRUE.
                    is_admin      = users.is_admin OR EXCLUDED.is_admin
            RETURNING id, email, display_name, karma_score, is_admin
        """),
        {
            "sub": google_sub, "email": email, "name": name,
            "avatar": avatar, "is_admin": is_bootstrap_admin,
        },
    )
    await db.commit()
    user = result.mappings().first()

    if is_bootstrap_admin:
        logger.info("admin.bootstrap.promoted email=%s", email)

    access_token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/callback?token={access_token}",
        status_code=302,
    )


@app.get("/api/auth/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ─────────────────────────────────────────────
#  Routes · Knowledge Base Search (Fuzzy)
# ─────────────────────────────────────────────
@app.get("/api/kb/search", response_model=list[KBArticleOut])
async def search_kb(
    q: str = Query(default="", max_length=200),
    manufacturer: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Fuzzy search using pg_trgm similarity + full-text fallback.
    Priority: similarity score > full-text rank > created_at.

    Response now includes error_codes[] and scenario_type (migration 004).
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    sql = """
        SELECT
            kb.id,
            kb.manufacturer_id,
            m.display_name  AS manufacturer_name,
            kb.title,
            kb.description,
            kb.source_url,
            kb.tags,
            kb.status,
            kb.error_codes,
            kb.scenario_type,
            kb.created_at,
            rs.resolution_score,
            rs.total_votes,
            CASE
                WHEN :q = '' THEN 1.0
                ELSE GREATEST(
                    similarity(kb.title,       :q),
                    similarity(kb.description, :q)
                )
            END AS sim_score
        FROM knowledge_base kb
        JOIN manufacturers m   ON m.id = kb.manufacturer_id
        LEFT JOIN kb_resolution_scores rs ON rs.kb_id = kb.id
        WHERE
            (:q = '' OR
                similarity(kb.title, :q) > 0.15 OR
                similarity(kb.description, :q) > 0.10 OR
                kb.fts_vector @@ plainto_tsquery('english', :q)
            )
            AND (:manufacturer IS NULL OR m.slug = :manufacturer)
            AND (:status_f IS NULL OR kb.status::TEXT = :status_f)
            AND (:tags_empty OR kb.tags @> :tag_arr::TEXT[])
        ORDER BY sim_score DESC, kb.created_at DESC
        LIMIT :limit OFFSET :offset
    """

    result = await db.execute(
        text(sql),
        {
            "q": q,
            "manufacturer": manufacturer,
            "status_f": status_filter,
            "tags_empty": len(tag_list) == 0,
            "tag_arr": tag_list,
            "limit": limit,
            "offset": offset,
        },
    )
    return [dict(row) for row in result.mappings().all()]


@app.get("/api/kb/{kb_id}", response_model=KBArticleOut)
async def get_kb_article(kb_id: UUID4, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
            SELECT kb.id, kb.manufacturer_id,
                   m.display_name AS manufacturer_name,
                   kb.title, kb.description, kb.source_url,
                   kb.tags, kb.status,
                   kb.error_codes, kb.scenario_type,
                   kb.created_at,
                   rs.resolution_score, rs.total_votes
            FROM knowledge_base kb
            JOIN manufacturers m ON m.id = kb.manufacturer_id
            LEFT JOIN kb_resolution_scores rs ON rs.kb_id = kb.id
            WHERE kb.id = :id
        """),
        {"id": str(kb_id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count (best-effort, non-blocking for response shape)
    await db.execute(
        text("UPDATE knowledge_base SET view_count = view_count + 1 WHERE id = :id"),
        {"id": str(kb_id)},
    )
    await db.commit()
    return dict(row)


# ─────────────────────────────────────────────
#  Routes · Error-Code Lookup (migration 004, GIN index)
# ─────────────────────────────────────────────
@app.get("/api/kb/by-error-code/{code}", response_model=list[KBArticleOut])
async def search_by_error_code(
    code: str,
    exact: bool = Query(
        default=True,
        description=(
            "True: GIN-indexed containment match (O(log n), case-sensitive). "
            "False: case-insensitive fallback via unnest()."
        ),
    ),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Exact and case-insensitive lookup on knowledge_base.error_codes.

    Matching strategy:
      exact=TRUE  → uses GIN index (kb.error_codes @> ARRAY[:code])
      exact=FALSE → case-insensitive via error_codes_ci_contains() helper
                    (still bounded by idx_kb_has_error_codes partial index)

    Returns empty list if no match; never 404. A 404 would be ambiguous
    between "unknown code" and "code with zero articles yet".
    """
    needle = code.strip().upper()
    if not needle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error code cannot be empty",
        )
    if len(needle) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error code too long (max 64 chars)",
        )

    if exact:
        where = "kb.error_codes @> ARRAY[:code]::TEXT[]"
    else:
        where = (
            "array_length(kb.error_codes, 1) > 0 "
            "AND error_codes_ci_contains(kb.error_codes, :code)"
        )

    sql = f"""
        SELECT
            kb.id, kb.manufacturer_id,
            m.display_name AS manufacturer_name,
            kb.title, kb.description, kb.source_url,
            kb.tags, kb.status,
            kb.error_codes, kb.scenario_type,
            kb.created_at,
            rs.resolution_score, rs.total_votes
        FROM knowledge_base kb
        JOIN manufacturers m               ON m.id    = kb.manufacturer_id
        LEFT JOIN kb_resolution_scores rs  ON rs.kb_id = kb.id
        WHERE {where}
        ORDER BY rs.resolution_score DESC NULLS LAST, kb.created_at DESC
        LIMIT :limit
    """

    result = await db.execute(text(sql), {"code": needle, "limit": limit})
    rows = [dict(r) for r in result.mappings().all()]

    logger.info(
        "kb.lookup.by_error_code code=%s exact=%s hits=%d",
        needle, exact, len(rows),
    )
    return rows


# ─────────────────────────────────────────────
#  Routes · Error-Code Statistics (migration 004)
# ─────────────────────────────────────────────
@app.get("/api/kb/error-codes/stats", response_model=ErrorCodeStatsResponse)
async def error_code_stats(
    response: Response,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Top N error codes across the knowledge base, plus global counters.

    Implementation notes:
      - unnest() expands error_codes into one row per code.
      - CROSS JOIN LATERAL preserves the source row so we can count
        distinct vendors per code.
      - GROUP BY + COUNT aggregates frequency.
      - Totals are cheap enough to inline in the same statement via CTE.
      - Cache-Control: 60s — aggregates are staleness-tolerant, and this
        endpoint is a natural candidate for dashboard polling.
    """
    sql = """
        WITH exploded AS (
            SELECT
                kb.id           AS article_id,
                m.slug          AS vendor,
                upper(trim(c))  AS code
            FROM   knowledge_base kb
            JOIN   manufacturers  m ON m.id = kb.manufacturer_id
            CROSS JOIN LATERAL unnest(kb.error_codes) AS c
            WHERE  array_length(kb.error_codes, 1) > 0
              AND  trim(c) <> ''
        ),
        ranked AS (
            SELECT
                code,
                COUNT(*)                                 AS frequency,
                array_agg(DISTINCT vendor ORDER BY vendor) AS vendors,
                (array_agg(article_id))[1]               AS sample_article_id
            FROM   exploded
            GROUP BY code
        ),
        totals AS (
            SELECT
                (SELECT COUNT(*) FROM ranked)                     AS total_unique_codes,
                (SELECT COALESCE(SUM(frequency), 0) FROM ranked)  AS total_code_uses,
                (SELECT COUNT(*) FROM knowledge_base
                 WHERE array_length(error_codes, 1) > 0)          AS articles_with_codes
        )
        SELECT
            (SELECT total_unique_codes  FROM totals)  AS total_unique_codes,
            (SELECT total_code_uses     FROM totals)  AS total_code_uses,
            (SELECT articles_with_codes FROM totals)  AS articles_with_codes,
            r.code, r.frequency, r.vendors, r.sample_article_id
        FROM   ranked r
        ORDER BY r.frequency DESC, r.code ASC
        LIMIT  :limit
    """

    result = await db.execute(text(sql), {"limit": limit})
    rows = result.mappings().all()

    response.headers["Cache-Control"] = "public, max-age=60"

    if not rows:
        # Still need totals when no rows (e.g. empty KB)
        totals_result = await db.execute(
            text("""
                SELECT
                    0 AS total_unique_codes,
                    0 AS total_code_uses,
                    (SELECT COUNT(*) FROM knowledge_base
                     WHERE array_length(error_codes, 1) > 0) AS articles_with_codes
            """)
        )
        totals = totals_result.mappings().first()
        return ErrorCodeStatsResponse(
            total_unique_codes=totals["total_unique_codes"],
            total_code_uses=totals["total_code_uses"],
            articles_with_codes=totals["articles_with_codes"],
            top=[],
        )

    first = rows[0]
    payload = ErrorCodeStatsResponse(
        total_unique_codes=first["total_unique_codes"],
        total_code_uses=first["total_code_uses"],
        articles_with_codes=first["articles_with_codes"],
        top=[
            ErrorCodeStat(
                code=r["code"],
                frequency=r["frequency"],
                vendors=list(r["vendors"] or []),
                sample_article_id=r["sample_article_id"],
            )
            for r in rows
        ],
    )

    logger.info(
        "kb.error_codes.stats limit=%d unique=%d total_uses=%d",
        limit, payload.total_unique_codes, payload.total_code_uses,
    )
    return payload


# ─────────────────────────────────────────────
#  Routes · Voting (protected)
# ─────────────────────────────────────────────
@app.post("/api/kb/vote", status_code=status.HTTP_201_CREATED)
async def cast_vote(
    payload: VoteIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Insert or update the user's vote on a KB article."""
    await db.execute(
        text("""
            INSERT INTO interactions (kb_id, user_id, vote)
            VALUES (:kb_id, :user_id, :vote)
            ON CONFLICT (user_id, kb_id) DO UPDATE SET vote = EXCLUDED.vote
        """),
        {"kb_id": str(payload.kb_id), "user_id": current_user["id"], "vote": payload.vote},
    )
    await db.commit()

    result = await db.execute(
        text("SELECT resolution_score, total_votes FROM kb_resolution_scores WHERE kb_id = :id"),
        {"id": str(payload.kb_id)},
    )
    row = result.mappings().first()
    return {
        "kb_id": str(payload.kb_id),
        "vote": payload.vote,
        "resolution_score": row["resolution_score"] if row else None,
        "total_votes": row["total_votes"] if row else 0,
    }


# ─────────────────────────────────────────────
#  Routes · Academy
# ─────────────────────────────────────────────
@app.get("/api/academy", response_model=list[AcademyResourceOut])
async def list_academy(
    certification: Optional[str] = Query(default=None),
    level: Optional[str] = Query(default=None),
    is_free: Optional[bool] = Query(default=None),
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    sql = """
        SELECT id, certification, level, title, description,
               resource_url, status, tags, is_free
        FROM academy_resources
        WHERE
            (:q = '' OR similarity(title, :q) > 0.15)
            AND (:cert IS NULL OR certification::TEXT = :cert)
            AND (:level IS NULL OR level::TEXT = :level)
            AND (:free IS NULL OR is_free = :free)
        ORDER BY
            CASE level
                WHEN 'beginner'     THEN 1
                WHEN 'associate'    THEN 2
                WHEN 'professional' THEN 3
                WHEN 'expert'       THEN 4
            END,
            certification
        LIMIT :limit
    """
    result = await db.execute(
        text(sql),
        {"q": q, "cert": certification, "level": level, "free": is_free, "limit": limit},
    )
    return [dict(r) for r in result.mappings().all()]


# ─────────────────────────────────────────────
#  Admin router — gated endpoints (/api/admin/*)
# ─────────────────────────────────────────────
#
# Imported AFTER the shared deps (engine, AsyncSessionLocal, get_db,
# get_current_user, run_link_health_check) are defined above, because
# admin.py imports them from this module.
#
from admin import router as admin_router  # noqa: E402

app.include_router(admin_router)
