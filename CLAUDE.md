# Tech-Fix-Bible — Contexto para Claude Code

## Rol
Senior Full-Stack Architect + DevOps. Colaborador técnico de un Ingeniero
de Infraestructura experto en entornos críticos (VMware, NSX, Networking, 
Splunk).

## Arquitectura
- backend/  — FastAPI + asyncpg + APScheduler
- frontend/ — Next.js 14 App Router + next-intl + Tailwind
- database/ — PostgreSQL 16 con pg_trgm, citext, uuid-ossp
- Despliegue: Vercel (frontend) + Railway (backend + DB)

## Principios del proyecto
1. URLs de fabricantes son la "única fuente de verdad". La validación de 
integridad de links es el corazón del proyecto.
2. Backend y frontend estrictamente separados.
3. Sistema de votación = motor de scoring (Resolution Score), no contador.
4. SEO de ingeniería: JSON-LD TechArticle + FAQPage en cada artículo.

## Estilo de código
- Backend: Pydantic, async, logs detallados, link checker no bloquea API.
- Frontend: TypeScript, Tailwind dashboard-like, auth via HttpOnly cookies 
(NO localStorage).
- DB: PostgreSQL con pg_trgm para fuzzy search.

## Estado actual — Patch v1.2 pendiente de aplicar
En sesiones previas del chat web se generó un patch v1.2 empaquetado en 
techkb-patch-v1.2.zip (raíz del repo). Aún no está aplicado.

Resumen del patch v1.2:
- Backend P0 hotfixes: scheduler no comparte AsyncSession entre ticks, 
karma trigger maneja INSERT/UPDATE/DELETE, health-check usa la columna 
correcta por tabla, JWT en cookie HttpOnly.
- DB: enum cert_name → tabla certifications con 19 certs seeded (PCNSA, 
PCNSE, NSE4, NSE7 incluidos; GCP_ACE incluido en cloud además de AWS_SA y 
AZ_104).
- Frontend: cookie auth, dynamic catalogs, JSON-LD inline, sitemap+robots 
con hreflang, i18n estricto.

## Reglas de trabajo
- Antes de cambios destructivos en DB: pg_dump del estado actual.
- Migraciones primero local, después prod.
- Commits descriptivos, una responsabilidad por commit.
- Mostrar git status y git diff --stat antes de commitear.
- Esperar OK explícito del usuario antes de hacer commit o push.
- Si una migración SQL aborta con RAISE EXCEPTION, NO hacer workaround: 
reportar al usuario con la query de inspección que dice el error.

## Plan v1.2.1 — orden estricto

PASO 1 ✓ — Migraciones 005 y 006 al repo (NO aplicadas).
PASO 2 — backend/main.py: hotfixes (cookies, endpoints nuevos, is_admin)
         + adaptar /api/academy a la FK certifications.
         + cablear admin router (include_router).
         Reparar admin.py: run_link_health_check() sin arg, is_admin en SELECT.
PASO 3 — seed_runner.py + seed_data.py: re-mapear certification string a
         certification_id UUID via lookup en la tabla certifications.
PASO 4 — Correr migraciones 005 y 006 contra DB local.
PASO 5 — Smoke test: uvicorn + curl /api/academy + /api/manufacturers
         + /api/certifications + /api/health.
PASO 6 — Frontend: AuthContext, Header, KBSearch, academy page,
         sitemap, robots, layouts, i18n, lib/api.ts.
