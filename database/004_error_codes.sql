-- ============================================================
--  Migration 004 · error_codes and scenario_type
--  Requires: 003_is_admin_and_manufacturers.sql applied
--  Idempotent — safe to re-run
-- ============================================================

-- 1. New columns ───────────────────────────────────────────────
ALTER TABLE knowledge_base
    ADD COLUMN IF NOT EXISTS error_codes    TEXT[]  NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS scenario_type  TEXT;

-- 2. Constraint on scenario_type (CHECK, not enum — keeps it flexible)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_kb_scenario_type'
    ) THEN
        ALTER TABLE knowledge_base
            ADD CONSTRAINT chk_kb_scenario_type
            CHECK (scenario_type IS NULL OR scenario_type IN (
                'troubleshooting',
                'integration',
                'hardening',
                'migration',
                'reference'
            ));
    END IF;
END $$;

-- 3. GIN index for array containment (@>) and overlap (&&) queries
--    Uses array_ops because we match exact codes, not partial strings.
CREATE INDEX IF NOT EXISTS idx_kb_error_codes
    ON knowledge_base USING GIN (error_codes);

-- 4. Partial index for "has any error code" filter — much smaller than
--    a full column index; used by the frontend "Only errors" checkbox.
CREATE INDEX IF NOT EXISTS idx_kb_has_error_codes
    ON knowledge_base (id)
    WHERE array_length(error_codes, 1) > 0;

-- 5. Btree index for scenario_type filter
CREATE INDEX IF NOT EXISTS idx_kb_scenario_type
    ON knowledge_base (scenario_type)
    WHERE scenario_type IS NOT NULL;

-- 6. Case-insensitive lookup helper function
--    Usage: SELECT * FROM knowledge_base WHERE error_codes_ci_contains(error_codes, 'spl-001');
CREATE OR REPLACE FUNCTION error_codes_ci_contains(codes TEXT[], needle TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
PARALLEL SAFE
AS $$
    SELECT EXISTS (
        SELECT 1 FROM unnest(codes) c WHERE upper(c) = upper(needle)
    );
$$;
