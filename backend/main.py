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
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from pydantic import UUID4, BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    payload = decode_token(auth_header.split(" ", 1)[1])
    user_id = payload.get("sub")

    result = await db.execute(
        text("SELECT id, email, display_name, karma_score FROM users WHERE id = :id AND is_active = TRUE"),
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

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
#  Pydantic Schemas  (Pydantic v2, lenient URL handling)
# ─────────────────────────────────────────────
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


class AcademyResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    certification: str
    level: str
    title: str
    description: str
    resource_url: str
    status: str
    tags: list[str]
    is_free: bool


class UserOut(BaseModel):
    id: UUID4
    email: str
    display_name: str
    karma_score: int


# ─────────────────────────────────────────────
#  Routes · Health
# ─────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


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

    # Return updated resolution score
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
        SELECT
            id,
            certification::TEXT AS certification,
            level::TEXT         AS level,
            title,
            description,
            resource_url,
            status::TEXT        AS status,
            tags,
            is_free
        FROM academy_resources
        WHERE
            (:q = '' OR similarity(title, :q) > 0.15)
            AND (:cert IS NULL OR certification::TEXT = :cert)
            AND (:level IS NULL OR level::TEXT = :level)
            AND (:free IS NULL OR is_free = :free)
        ORDER BY
            CASE level::TEXT
                WHEN 'beginner'     THEN 1
                WHEN 'associate'    THEN 2
                WHEN 'professional' THEN 3
                WHEN 'expert'       THEN 4
            END,
            certification::TEXT
        LIMIT :limit
    """
    result = await db.execute(
        text(sql),
        {"q": q, "cert": certification, "level": level, "free": is_free, "limit": limit},
    )
    return [dict(r) for r in result.mappings().all()]


# ─────────────────────────────────────────────
#  Routes · Admin: Manual Link Health Check
# ─────────────────────────────────────────────
@app.post("/api/admin/health-check")
async def manual_health_check(
    current_user: dict = Depends(get_current_user),
):
    """Trigger a manual link health check (admin only, extend with role check)."""
    asyncio.create_task(run_link_health_check())
    return {"message": "Health check started in background"}
