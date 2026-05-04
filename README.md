# Tech-Fix-Bible

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://postgresql.org)
[![GIN Index](https://img.shields.io/badge/Search-GIN%20O(log%20n)-d29922)](#search-engine)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Centralized, bilingual (EN/ES) technical knowledge base for infrastructure
> engineers. Indexes vendor error codes and integration scenarios across
> **12 vendors · 48 curated articles · 143 mapped error codes**.


## 🚀 Live Deployment

| Component | URL | Status |
|-----------|-----|--------|
| Frontend (Next.js) | https://tech-fix-bible.vercel.app | 🟢 Live |
| Backend API (FastAPI) | https://tech-fix-bible-production.up.railway.app | 🟢 Live |
| API Docs (Swagger) | https://tech-fix-bible-production.up.railway.app/api/docs | 🟢 Live |
| Database | Railway Postgres 18.3 | 🟢 Live |
| Backups | GitHub Releases (daily 03:00 UTC) | 🟢 Automated |

**Stage 1 (MVP) shipped.** See `scripts/` for ops tooling: `apply_migrations.sh`, `seed_kb_articles.sql`, `backup_db.sh`, `restore_db.sh`.

---
---

## Why this exists

Vendor documentation rots. Links break silently. Error codes live in PDFs
nobody reads. An engineer hitting `FSLOGIX-26` at 2 AM shouldn't have to
pivot across five tabs to figure out what it means.

Tech-Fix-Bible solves three problems in one platform:

1. **Link integrity** — every source URL is probed by an async HEAD-request
   scheduler. Broken links surface in the admin dashboard within hours.
2. **Error-code discoverability** — search by `HTTP-429`, `VSX-ISL-DOWN`,
   or `IDRAC-SUP0516` returns the article in O(log n) via a **GIN index**,
   not a full-text scan.
3. **Community-validated resolution** — likes and dislikes drive a live
   **Resolution Score**; low scores are a red flag that the article needs
   a rewrite.

---

## Search engine

The lookup pipeline is intentionally layered for performance and recall.

| Query shape                    | Index used                 | Complexity | Typical latency (48 docs) |
|--------------------------------|----------------------------|------------|---------------------------|
| `error_codes @> ARRAY['X']`    | `idx_kb_error_codes` GIN   | O(log n)   | < 1 ms                    |
| `similarity(title, 'ospf')`    | `idx_kb_title_trgm` GIN    | O(log n)   | ~ 2 ms                    |
| `fts_vector @@ plainto_tsquery`| `idx_kb_fts` GIN           | O(log n)   | ~ 2 ms                    |
| `tags @> ARRAY['vsan']`        | `idx_kb_tags` GIN          | O(log n)   | < 1 ms                    |
| `WHERE is_admin = TRUE`        | Partial B-tree             | O(1)       | < 1 ms                    |

**Why GIN over B-tree for arrays?** B-tree can't index `TEXT[]` containment;
you'd scan every row and `unnest()` each. GIN stores an inverted map from
each element to the rows that contain it — same data structure Elasticsearch
uses internally. At 10k articles, the exact-code lookup still finishes in
under 5 ms.

See `database/004_error_codes.sql` for the full DDL, including the partial
index `idx_kb_has_error_codes` that powers the frontend "Only errors" filter
without a sequential scan.

---

## Maturity metrics

The admin dashboard exposes three signals that track content health:

```
unique_codes       = COUNT(DISTINCT code)                           — diversity
total_code_uses    = SUM(frequency)                                 — volume
enrichment_ratio   = total_code_uses / articles_with_codes          — depth
```

**Current state:**

```
┌────────────────────────────────────────────────────────┐
│  Vendor       Articles  Error codes                    │
│  ────────────────────────────────────────              │
│  citrix         5           21                         │
│  hpe            6           18                         │
│  aruba          6           18                         │
│  dell           6           18                         │
│  splunk         5           15                         │
│  cisco          4           13                         │
│  vmware         4           12                         │
│  paloalto       3            7                         │
│  fortinet       3            7                         │
│  checkpoint     2            5                         │
│  juniper        2            5                         │
│  f5             2            4                         │
│  ────────────────────────────────────────              │
│  TOTAL         48          143                         │
│                                                        │
│  enrichment_ratio = 143 / 48 = 2.98 codes/article     │
└────────────────────────────────────────────────────────┘
```

Target: keep `enrichment_ratio > 2.5`. When it falls, new content is
landing without proper error-code mapping.

---

## Architecture

```
┌─────────────────────────────────┐
│  Vercel · Next.js 14 (App Dir)  │  SSR/ISR · i18n EN/ES · JSON-LD
└──────────────┬──────────────────┘
               │ REST · HTTPS
┌──────────────▼──────────────────┐
│  Railway · FastAPI              │  OAuth2 · JWT · APScheduler · httpx
│  ┌───────────────────────────┐  │
│  │  Admin Router             │  │   is_admin gate · audit_log
│  │  /api/admin/*             │  │
│  └───────────────────────────┘  │
└──────────────┬──────────────────┘
               │ asyncpg
┌──────────────▼──────────────────┐
│  PostgreSQL 16                  │  pg_trgm · GIN × 6 · FTS · triggers
└─────────────────────────────────┘
```

---

## Repository layout

```
Tech-Fix-Bible/
├── backend/          FastAPI app, admin router, seed runner
├── database/         Versioned SQL migrations (schema + 003 + 004)
├── frontend/         Next.js 14 App Router, i18n, components
└── scripts/          deploy.sh + healthcheck.sh
```

---

## Quickstart

### Prerequisites

| Tool        | Minimum | Notes                                      |
|-------------|---------|--------------------------------------------|
| PostgreSQL  | 14      | 16 recommended                             |
| Python      | 3.11    | FastAPI requires modern typing             |
| Node.js     | 20 LTS  | Next.js 14                                 |
| pnpm / npm  | latest  | lockfile your choice                       |

### 1 · Database

```bash
createdb tech_fix_bible
export DATABASE_URL='postgresql://user:pass@localhost:5432/tech_fix_bible'

# Applies migrations in order, then seeds 48 articles + 10 academy
./scripts/deploy.sh
```

### 2 · Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in SECRET_KEY, Google OAuth, ADMIN_EMAILS

uvicorn main:app --reload --port 8000
# Swagger UI → http://localhost:8000/api/docs
```

### 3 · Frontend

```bash
cd frontend
pnpm install
cp .env.local.example .env.local
pnpm dev
# → http://localhost:3000
```

### 4 · Smoke test

```bash
./scripts/healthcheck.sh                                     # local
API_URL=https://your-api.railway.app ./scripts/healthcheck.sh # remote
```

---

## API reference

| Method | Path                                | Auth  | Purpose                           |
|--------|-------------------------------------|-------|-----------------------------------|
| GET    | `/api/health`                       | —     | Liveness probe                    |
| GET    | `/api/kb/search`                    | —     | Fuzzy search (title + tags + FTS) |
| GET    | `/api/kb/{id}`                      | —     | Article detail + increment views  |
| GET    | `/api/kb/by-error-code/{code}`      | —     | **GIN-indexed** error-code lookup |
| GET    | `/api/kb/error-codes/stats`         | —     | Top N codes · vendor breakdown    |
| POST   | `/api/kb/vote`                      | JWT   | Like / dislike                    |
| GET    | `/api/academy`                      | —     | Certification resources           |
| GET    | `/api/auth/login`                   | —     | Google OAuth2 redirect            |
| GET    | `/api/auth/callback`                | —     | OAuth callback → JWT              |
| GET    | `/api/auth/me`                      | JWT   | Current user profile              |
| POST   | `/api/admin/seed`                   | admin | Idempotent reseed                 |
| POST   | `/api/admin/health-check`           | admin | Trigger async link checker        |
| GET    | `/api/admin/audit`                  | admin | Recent admin actions              |
| POST   | `/api/admin/users/{id}/grant`       | admin | Promote admin                     |
| POST   | `/api/admin/users/{id}/revoke`      | admin | Revoke admin (last-admin guard)   |

---

## Admin bootstrap

First admin is promoted automatically via `ADMIN_EMAILS` env var on Google
OAuth login. **Env is promote-only** — revocation is always DB-driven:

```bash
# Via API
curl -X POST -H "Authorization: Bearer $TOKEN" \
    https://api.example.com/api/admin/users/{id}/revoke

# Or directly in SQL
psql $DATABASE_URL -c "UPDATE users SET is_admin = FALSE WHERE email = 'ex@example.com';"
```

Last-admin guard prevents lockout: the platform refuses to revoke if it
would leave zero active admins.

---

## SEO · Schema.org rich snippets

Each KB article page injects two JSON-LD blocks:

- **FAQPage** — Google renders expandable Q/A in SERPs
- **TechArticle** with `AggregateRating` derived from resolution score

Validate at [search.google.com/test/rich-results](https://search.google.com/test/rich-results).

---

## License

MIT © Tech-Fix-Bible Contributors
