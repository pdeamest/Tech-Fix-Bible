-- ============================================================
--  Migration 003 · is_admin flag + HPE/Dell manufacturers
--  Idempotent — safe to re-run
-- ============================================================

-- 1. Admin flag on users ───────────────────────────────────────
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- Partial index — only admin rows hit it, DB stays slim
CREATE INDEX IF NOT EXISTS idx_users_is_admin
    ON users (is_admin) WHERE is_admin = TRUE;

-- 2. Manufacturer gaps ─────────────────────────────────────────
--    schema.sql ships vmware, cisco, paloalto, fortinet, checkpoint,
--    juniper, aruba, f5. We add hpe and dell so the HPE/Aruba/Dell
--    batch can be seeded.  Aruba is already there; hpe/dell are new.
INSERT INTO manufacturers (slug, display_name, website_url) VALUES
    ('hpe',  'Hewlett Packard Enterprise', 'https://support.hpe.com'),
    ('dell', 'Dell Technologies',          'https://www.dell.com/support')
ON CONFLICT (slug) DO NOTHING;

-- 3. Tag table_name on audit_log for fast admin filtering ──────
CREATE INDEX IF NOT EXISTS idx_audit_table_created
    ON audit_log (table_name, created_at DESC);
