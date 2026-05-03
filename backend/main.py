"""
KB Platform · FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from dotenv import load_dotenv
load_dotenv()  # must run before any os.environ[...] below

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from pydantic import UUID4, BaseModel, ConfigDict, HttpUrl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.middleware.sessions import SessionMiddleware

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
DATABASE_URL   = os.environ["DATABASE_URL"]          # postgresql+asyncpg://user:pass@host/db
# Railway/Heroku give us postgresql://; sqlalchemy + asyncpg needs postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
SECRET_KEY     = os.environ["SECRET_KEY"]            # openssl rand -hex 32
ALGORITHM      = "HS256"
TOKEN_EXPIRE   = 60 * 24 * 7                         # minutes → 7 days
FRONTEND_URL   = os.environ.get("FRONTEND_URL", "http://localhost:3000")
HEALTH_CHECK_INTERVAL_HOURS = int(os.environ.get("HEALTH_CHECK_HOURS", "6"))
ENVIRONMENT    = os.environ.get("ENVIRONMENT", "development")

# Bootstrap admins by email (CSV). Matched users get is_admin=TRUE on every
# Google login. Revocation must be done in DB (UPDATE users SET is_admin=FALSE);
# removing an email from this var alone does NOT demote — by design.
ADMIN_EMAILS = {
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "").split(",")
    if e.strip()
}

COOKIE_NAME    = "kb_session"
COOKIE_SECURE  = ENVIRONMENT == "production"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kb-platform")

# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# ─────────────────────────────────────────────
#  JWT helpers
# ─────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=TOKEN_EXPIRE * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(token)
    user_id = payload.get("sub")

    result = await db.execute(
        text("SELECT id, email, display_name, karma_score, is_admin FROM users WHERE id = :id AND is_active = TRUE"),
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
    client_id=os.environ.get("GOOGLE_CLIENT_ID", "placeholder"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", "placeholder"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# ─────────────────────────────────────────────
#  Async Link Health Checker
# ─────────────────────────────────────────────
# Each table has a different URL column name — keep them mapped here.
URL_COLUMNS = {
    "knowledge_base":    "source_url",
    "academy_resources": "resource_url",
}


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


async def run_link_health_check() -> None:
    """
    Checks all KB articles and Academy resources; updates status in DB.
    Opens its own DB session so it can run safely from the scheduler.
    """
    logger.info("Starting link health check …")

    async with AsyncSessionLocal() as db:
        for table, url_col in URL_COLUMNS.items():
            result = await db.execute(
                text(f"SELECT id, {url_col} AS url FROM {table}")  # noqa: S608
            )
            rows = result.fetchall()

            if not rows:
                continue

            tasks = [check_single_url(row.url) for row in rows]
            statuses = await asyncio.gather(*tasks, return_exceptions=True)

            for row, link_status in zip(rows, statuses):
                new_status = link_status if isinstance(link_status, str) else "broken"
                extra = ", last_health_check = NOW()" if table == "knowledge_base" else ""
                await db.execute(
                    text(f"UPDATE {table} SET status = :s{extra} WHERE id = :id"),  # noqa: S608
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
    scheduler.add_job(
        run_link_health_check,
        "interval",
        hours=HEALTH_CHECK_INTERVAL_HOURS,
        next_run_time=datetime.now() + timedelta(seconds=10),
    )
    scheduler.start()
    yield
    scheduler.shutdown()


# ─────────────────────────────────────────────
#  FastAPI App
# ─────────────────────────────────────────────
app = FastAPI(
    title="KB Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=COOKIE_SECURE,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin router. Imported here (not at the top) because admin.py does
# `from main import ...` — by this point engine, AsyncSessionLocal,
# get_db, get_current_user and run_link_health_check are all bound.
import admin  # noqa: E402

app.include_router(admin.router)


# ─────────────────────────────────────────────
#  Pydantic Schemas  (Pydantic v2, lenient URL handling)
# ─────────────────────────────────────────────
class ManufacturerOut(BaseModel):
    id: UUID4
    slug: str
    display_name: str
    website_url: str
    logo_url: Optional[str] = None


class CertificationOut(BaseModel):
    id: UUID4
    code: str
    display_name: str
    vendor_slug: Optional[str] = None
    icon: Optional[str] = None
    website_url: Optional[str] = None


class KBArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    manufacturer_id: UUID4
    manufacturer_name: str
    title: str
    description: str
    source_url: str
    tags: list[str]
    status: str
    resolution_score: Optional[float] = None
    total_votes: Optional[int] = None
    created_at: datetime


class VoteIn(BaseModel):
    kb_id: UUID4
    vote: Literal["like", "dislike"]


class VoteOut(BaseModel):
    kb_id: UUID4
    vote: Optional[Literal["like", "dislike"]] = None   # None when the vote was removed
    resolution_score: Optional[float] = None
    total_votes: int = 0


class AcademyResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    certification_code: str
    certification_name: str
    certification_icon: Optional[str] = None
    vendor_slug: Optional[str] = None
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
    is_admin: bool = False


# ─────────────────────────────────────────────
#  Routes · Health
# ─────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ─────────────────────────────────────────────
#  Routes · Catalog endpoints (dynamic dropdowns)
# ─────────────────────────────────────────────
@app.get("/api/manufacturers", response_model=list[ManufacturerOut])
async def list_manufacturers(db: AsyncSession = Depends(get_db)):
    """Vendor catalog. Consumed by KB filters and the create-article form."""
    result = await db.execute(
        text("""
            SELECT id, slug, display_name, website_url, logo_url
            FROM manufacturers
            ORDER BY display_name
        """)
    )
    return [dict(r) for r in result.mappings().all()]


@app.get("/api/certifications", response_model=list[CertificationOut])
async def list_certifications(
    vendor: Optional[str] = Query(default=None, description="Filter by vendor slug"),
    db: AsyncSession = Depends(get_db),
):
    """
    Certification catalog. Replaces the cert_name enum.
    Requires migration 006 to be applied — returns 500 otherwise.
    """
    result = await db.execute(
        text("""
            SELECT id, code, display_name, vendor_slug, icon, website_url
            FROM certifications
            WHERE is_active = TRUE
              AND (CAST(:vendor AS TEXT) IS NULL OR vendor_slug = :vendor)
            ORDER BY display_order, code
        """),
        {"vendor": vendor},
    )
    return [dict(r) for r in result.mappings().all()]


# ─────────────────────────────────────────────
#  Routes · Google OAuth2
# ─────────────────────────────────────────────
@app.get("/api/auth/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/api/auth/callback", name="google_callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token_data = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    user_info = token_data.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not retrieve user info from Google")

    google_sub  = user_info["sub"]
    email       = user_info["email"]
    name        = user_info.get("name", email.split("@")[0])
    avatar      = user_info.get("picture")

    # Upsert user
    result = await db.execute(
        text("""
            INSERT INTO users (google_sub, email, display_name, avatar_url, last_login_at)
            VALUES (:sub, :email, :name, :avatar, NOW())
            ON CONFLICT (google_sub) DO UPDATE
                SET last_login_at = NOW(),
                    avatar_url    = EXCLUDED.avatar_url
            RETURNING id, email, display_name, karma_score
        """),
        {"sub": google_sub, "email": email, "name": name, "avatar": avatar},
    )
    await db.commit()
    user = result.mappings().first()

    # Bootstrap admin promotion (idempotent). DB-only revocation, see ADMIN_EMAILS.
    if email.lower() in ADMIN_EMAILS:
        await db.execute(
            text("UPDATE users SET is_admin = TRUE WHERE google_sub = :sub"),
            {"sub": google_sub},
        )
        await db.commit()
        # Re-fetch so any downstream consumer of `user` sees the post-promotion state.
        # The JWT itself only carries sub+email, but get_current_user reads is_admin
        # fresh from DB on every request, so the next /api/auth/me reflects this.
        result = await db.execute(
            text(
                "SELECT id, email, display_name, karma_score, is_admin "
                "FROM users WHERE google_sub = :sub"
            ),
            {"sub": google_sub},
        )
        user = result.mappings().first()

    access_token = create_access_token({"sub": str(user["id"]), "email": user["email"]})

    response = RedirectResponse(url=f"{FRONTEND_URL}/", status_code=302)
    set_auth_cookie(response, access_token)
    return response


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Clears the kb_session cookie. Idempotent — no auth required."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookie(response)
    return response


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
    Fuzzy search using pg_trgm similarity + full-text search fallback.
    Priority: similarity score > full-text rank > created_at
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    sql = """
        SELECT
            kb.id,
            kb.manufacturer_id,
            m.display_name       AS manufacturer_name,
            kb.title,
            kb.description,
            kb.source_url,
            kb.tags,
            kb.status::TEXT      AS status,
            kb.created_at,
            rs.resolution_score,
            rs.total_votes,
            CASE
                WHEN CAST(:q AS TEXT) = '' THEN 1.0
                ELSE GREATEST(
                    similarity(kb.title,       CAST(:q AS TEXT)),
                    similarity(kb.description, CAST(:q AS TEXT))
                )
            END AS sim_score
        FROM knowledge_base kb
        JOIN manufacturers m   ON m.id = kb.manufacturer_id
        LEFT JOIN kb_resolution_scores rs ON rs.kb_id = kb.id
        WHERE
            (CAST(:q AS TEXT) = '' OR
                similarity(kb.title, CAST(:q AS TEXT)) > 0.15 OR
                similarity(kb.description, CAST(:q AS TEXT)) > 0.10 OR
                kb.fts_vector @@ plainto_tsquery('english', CAST(:q AS TEXT))
            )
            AND (CAST(:manufacturer AS TEXT) IS NULL OR m.slug = :manufacturer)
            AND (CAST(:status_f AS TEXT) IS NULL OR kb.status::TEXT = :status_f)
            AND (CAST(:tags_empty AS BOOLEAN) OR kb.tags @> CAST(:tag_arr AS TEXT[]))
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
    # Explicit column list — avoids leaking fts_vector, content_md, error_codes, etc.
    result = await db.execute(
        text("""
            SELECT
                kb.id,
                kb.manufacturer_id,
                m.display_name       AS manufacturer_name,
                kb.title,
                kb.description,
                kb.source_url,
                kb.tags,
                kb.status::TEXT      AS status,
                kb.created_at,
                rs.resolution_score,
                rs.total_votes
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

    # increment view count
    await db.execute(
        text("UPDATE knowledge_base SET view_count = view_count + 1 WHERE id = :id"),
        {"id": str(kb_id)},
    )
    await db.commit()
    return dict(row)


# ─────────────────────────────────────────────
#  Routes · Voting (protected)
# ─────────────────────────────────────────────
async def _resolution_for(db: AsyncSession, kb_id: str) -> tuple[Optional[float], int]:
    """Reads the current resolution_score / total_votes for a KB article."""
    result = await db.execute(
        text(
            "SELECT resolution_score, total_votes "
            "FROM kb_resolution_scores WHERE kb_id = :id"
        ),
        {"id": kb_id},
    )
    row = result.mappings().first()
    if not row:
        return (None, 0)
    return (row["resolution_score"], row["total_votes"])


@app.post("/api/kb/vote", response_model=VoteOut, status_code=status.HTTP_201_CREATED)
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
            ON CONFLICT (user_id, kb_id) DO UPDATE
                SET vote = EXCLUDED.vote
        """),
        {
            "kb_id":   str(payload.kb_id),
            "user_id": str(current_user["id"]),
            "vote":    payload.vote,
        },
    )
    await db.commit()

    score, total = await _resolution_for(db, str(payload.kb_id))
    return VoteOut(
        kb_id=payload.kb_id,
        vote=payload.vote,
        resolution_score=score,
        total_votes=total,
    )


@app.delete("/api/kb/vote/{kb_id}", response_model=VoteOut)
async def remove_vote(
    kb_id: UUID4,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retira el voto del usuario (undo). El trigger de karma (migración 005)
    reversa la contribución al karma_score automáticamente.
    """
    await db.execute(
        text("DELETE FROM interactions WHERE kb_id = :kb AND user_id = :u"),
        {"kb": str(kb_id), "u": str(current_user["id"])},
    )
    await db.commit()

    score, total = await _resolution_for(db, str(kb_id))
    return VoteOut(
        kb_id=kb_id,
        vote=None,
        resolution_score=score,
        total_votes=total,
    )


# ─────────────────────────────────────────────
#  Routes · Academy
# ─────────────────────────────────────────────
@app.get("/api/academy", response_model=list[AcademyResourceOut])
async def list_academy(
    certification: Optional[str] = Query(
        default=None, description="Certification code (e.g. CCNA, PCNSA)"
    ),
    level: Optional[str] = Query(default=None),
    is_free: Optional[bool] = Query(default=None),
    q: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Academy resource catalog joined with certifications.
    Requires migration 006 to be applied — returns 500 otherwise
    (column academy_resources.certification_id does not exist).
    """
    sql = """
        SELECT ar.id,
               c.code          AS certification_code,
               c.display_name  AS certification_name,
               c.icon          AS certification_icon,
               c.vendor_slug   AS vendor_slug,
               ar.level, ar.title, ar.description,
               ar.resource_url, ar.status, ar.tags, ar.is_free
        FROM   academy_resources ar
        JOIN   certifications    c ON c.id = ar.certification_id
        WHERE
            (:q = '' OR similarity(ar.title, :q) > 0.15)
            AND (CAST(:cert AS TEXT) IS NULL OR c.code         = :cert)
            AND (CAST(:level AS TEXT) IS NULL OR ar.level::TEXT = :level)
            AND (CAST(:free AS BOOLEAN) IS NULL OR ar.is_free     = :free)
            AND c.is_active = TRUE
        ORDER BY
            c.display_order,
            CASE ar.level
                WHEN 'beginner'     THEN 1
                WHEN 'associate'    THEN 2
                WHEN 'professional' THEN 3
                WHEN 'expert'       THEN 4
            END,
            ar.title
        LIMIT :limit
    """
    result = await db.execute(
        text(sql),
        {"q": q, "cert": certification, "level": level,
         "free": is_free, "limit": limit},
    )
    return [dict(r) for r in result.mappings().all()]


