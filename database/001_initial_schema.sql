-- ============================================================
--  Migration 001 · Initial schema
--  PostgreSQL >= 14 required
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Enums
CREATE TYPE link_status AS ENUM ('online', 'broken', 'unchecked');
CREATE TYPE vote_type   AS ENUM ('like', 'dislike');
CREATE TYPE cert_level  AS ENUM ('beginner', 'associate', 'professional', 'expert');
CREATE TYPE cert_name   AS ENUM ('VCP', 'CCNA', 'CCNP', 'CCIE', 'CISSP', 'CEH', 'AWS_SA', 'OTHER');

-- ── 1. USERS ─────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_sub      TEXT         UNIQUE NOT NULL,
    email           CITEXT       UNIQUE NOT NULL,
    display_name    TEXT         NOT NULL,
    avatar_url      TEXT,
    karma_score     INTEGER      NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);

CREATE INDEX idx_users_google_sub ON users (google_sub);
CREATE INDEX idx_users_email      ON users (email);

-- ── 2. MANUFACTURERS ─────────────────────────────────────────
CREATE TABLE manufacturers (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug         TEXT        UNIQUE NOT NULL,
    display_name TEXT        NOT NULL,
    logo_url     TEXT,
    website_url  TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_manufacturers_slug ON manufacturers (slug);

INSERT INTO manufacturers (slug, display_name, website_url) VALUES
    ('vmware',     'VMware by Broadcom',  'https://docs.vmware.com'),
    ('cisco',      'Cisco',               'https://www.cisco.com/c/en/us/support'),
    ('paloalto',   'Palo Alto Networks',  'https://docs.paloaltonetworks.com'),
    ('fortinet',   'Fortinet',            'https://docs.fortinet.com'),
    ('checkpoint', 'Check Point',         'https://sc1.checkpoint.com/documents/latest'),
    ('juniper',    'Juniper Networks',    'https://www.juniper.net/documentation'),
    ('aruba',      'Aruba Networks',      'https://www.arubanetworks.com/techdocs'),
    ('f5',         'F5 Networks',         'https://clouddocs.f5.com');

-- ── 3. KNOWLEDGE BASE ────────────────────────────────────────
CREATE TABLE knowledge_base (
    id                  UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id     UUID         NOT NULL REFERENCES manufacturers(id) ON DELETE RESTRICT,
    author_id           UUID         REFERENCES users(id) ON DELETE SET NULL,
    title               TEXT         NOT NULL,
    description         TEXT         NOT NULL,
    content_md          TEXT,
    source_url          TEXT         NOT NULL,
    tags                TEXT[]       NOT NULL DEFAULT '{}',
    status              link_status  NOT NULL DEFAULT 'unchecked',
    view_count          INTEGER      NOT NULL DEFAULT 0,
    last_health_check   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_kb_manufacturer     ON knowledge_base (manufacturer_id);
CREATE INDEX idx_kb_author           ON knowledge_base (author_id);
CREATE INDEX idx_kb_status           ON knowledge_base (status);
CREATE INDEX idx_kb_tags             ON knowledge_base USING GIN (tags);
CREATE INDEX idx_kb_title_trgm       ON knowledge_base USING GIN (title       gin_trgm_ops);
CREATE INDEX idx_kb_description_trgm ON knowledge_base USING GIN (description gin_trgm_ops);

ALTER TABLE knowledge_base
    ADD COLUMN fts_vector TSVECTOR
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title,       '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED;

CREATE INDEX idx_kb_fts ON knowledge_base USING GIN (fts_vector);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_kb_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── 4. INTERACTIONS (votes) ──────────────────────────────────
CREATE TABLE interactions (
    id         UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    kb_id      UUID         NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    user_id    UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vote       vote_type    NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_interaction_user_kb UNIQUE (user_id, kb_id)
);

CREATE INDEX idx_interactions_kb   ON interactions (kb_id);
CREATE INDEX idx_interactions_user ON interactions (user_id);

-- Karma trigger (defined AFTER knowledge_base and interactions exist)
CREATE OR REPLACE FUNCTION update_karma_on_vote()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    article_author UUID;
    delta          INTEGER;
BEGIN
    SELECT author_id INTO article_author
    FROM   knowledge_base
    WHERE  id = NEW.kb_id;

    delta := CASE WHEN NEW.vote = 'like' THEN 1 ELSE -1 END;

    UPDATE users
    SET    karma_score = karma_score + delta
    WHERE  id = article_author;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_karma_on_vote
    AFTER INSERT ON interactions
    FOR EACH ROW EXECUTE FUNCTION update_karma_on_vote();

-- Resolution Score view
CREATE OR REPLACE VIEW kb_resolution_scores AS
SELECT
    kb_id,
    COUNT(*)                                          AS total_votes,
    COUNT(*) FILTER (WHERE vote = 'like')             AS likes,
    COUNT(*) FILTER (WHERE vote = 'dislike')          AS dislikes,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE vote = 'like')
        / NULLIF(COUNT(*), 0)
    , 1)                                              AS resolution_score
FROM interactions
GROUP BY kb_id;

-- ── 5. ACADEMY ───────────────────────────────────────────────
CREATE TABLE academy_resources (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    certification   cert_name   NOT NULL,
    level           cert_level  NOT NULL,
    title           TEXT        NOT NULL,
    description     TEXT        NOT NULL,
    resource_url    TEXT        NOT NULL,
    status          link_status NOT NULL DEFAULT 'unchecked',
    tags            TEXT[]      NOT NULL DEFAULT '{}',
    is_free         BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_academy_cert       ON academy_resources (certification);
CREATE INDEX idx_academy_level      ON academy_resources (level);
CREATE INDEX idx_academy_tags       ON academy_resources USING GIN (tags);
CREATE INDEX idx_academy_title_trgm ON academy_resources USING GIN (title gin_trgm_ops);

INSERT INTO academy_resources (certification, level, title, description, resource_url, is_free, tags) VALUES
    ('VCP',  'associate',    'VMware vSphere Foundations Exam',
     'Official study guide for VCP-DCV 2024', 'https://www.vmware.com/learning/certification', TRUE,
     ARRAY['vsphere','vcenter','esxi']),
    ('CCNA', 'associate',    'Cisco CCNA 200-301 Complete Course',
     'Full Packet Tracer labs + theory', 'https://www.netacad.com', FALSE,
     ARRAY['routing','switching','ospf','vlans']),
    ('CISSP','professional', 'CISSP Official Study Guide 9th Ed.',
     'ISC2 official material covering all 8 domains', 'https://www.isc2.org/certifications/cissp', FALSE,
     ARRAY['security','iam','cryptography','risk']);

-- ── 6. AUDIT LOG ─────────────────────────────────────────────
CREATE TABLE audit_log (
    id          BIGSERIAL    PRIMARY KEY,
    table_name  TEXT         NOT NULL,
    record_id   UUID         NOT NULL,
    action      TEXT         NOT NULL,
    changed_by  UUID         REFERENCES users(id),
    diff        JSONB,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_table_record ON audit_log (table_name, record_id);
