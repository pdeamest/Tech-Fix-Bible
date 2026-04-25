-- ============================================================
--  Migration 006 · ENUM cert_name → tabla certifications (originally 002 in patch v1.2)
--
--  Motivo: el enum no escala. Agregar un cert nuevo (PCNSA, NSE7)
--  requiere ALTER TYPE ADD VALUE y deploy. Una tabla con seed es
--  más limpia, soporta metadata (icon, vendor, order) y permite
--  deshabilitar certs sin migraciones.
--
--  Transaccional + verificación antes del drop destructivo.
-- ============================================================

BEGIN;

-- ────────────────────────────────────────────────────────────
--  1. Tabla nueva
-- ────────────────────────────────────────────────────────────
CREATE TABLE certifications (
    id            UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    code          TEXT         UNIQUE NOT NULL,     -- VCP, CCNA, PCNSA…
    display_name  TEXT         NOT NULL,
    vendor_slug   TEXT         REFERENCES manufacturers(slug) ON DELETE SET NULL,
    icon          TEXT,                              -- emoji corto
    website_url   TEXT,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    display_order INTEGER      NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_certifications_code   ON certifications (code);
CREATE INDEX idx_certifications_active ON certifications (is_active);
CREATE INDEX idx_certifications_order  ON certifications (display_order);

-- ────────────────────────────────────────────────────────────
--  2. Seed del catálogo completo
--     (cubre lo que ya tenías + lo que el frontend usaba sin
--     soporte en DB: PCNSA, NSE4, más variantes avanzadas)
-- ────────────────────────────────────────────────────────────
INSERT INTO certifications (code, display_name, vendor_slug, icon, display_order) VALUES
    -- VMware
    ('VCP',     'VMware Certified Professional',                              'vmware',     '🔵', 10),
    ('VCAP',    'VMware Certified Advanced Professional',                     'vmware',     '🔷', 11),
    ('VCDX',    'VMware Certified Design Expert',                             'vmware',     '💎', 12),
    -- Cisco
    ('CCNA',    'Cisco Certified Network Associate',                          'cisco',      '🌐', 20),
    ('CCNP',    'Cisco Certified Network Professional',                       'cisco',      '🌐', 21),
    ('CCIE',    'Cisco Certified Internetwork Expert',                        'cisco',      '🌐', 22),
    -- Palo Alto
    ('PCNSA',   'Palo Alto Certified Network Security Administrator',         'paloalto',   '🟠', 30),
    ('PCNSE',   'Palo Alto Certified Network Security Engineer',              'paloalto',   '🟠', 31),
    -- Fortinet
    ('NSE4',    'Fortinet NSE 4 — Network Security Professional',             'fortinet',   '🔴', 40),
    ('NSE7',    'Fortinet NSE 7 — Advanced Analyst',                           'fortinet',   '🔴', 41),
    -- Juniper
    ('JNCIA',   'Juniper Networks Certified Associate',                       'juniper',    '🟢', 50),
    ('JNCIP',   'Juniper Networks Certified Professional',                    'juniper',    '🟢', 51),
    -- Check Point
    ('CCSA',    'Check Point Certified Security Administrator',               'checkpoint', '🔶', 60),
    ('CCSE',    'Check Point Certified Security Expert',                      'checkpoint', '🔶', 61),
    -- Security vendor-agnostic
    ('CISSP',   'Certified Information Systems Security Professional',        NULL,         '🔒', 70),
    ('CEH',     'Certified Ethical Hacker',                                   NULL,         '⚔️', 71),
    -- Cloud
    ('AWS_SA',  'AWS Certified Solutions Architect',                          NULL,         '☁️', 80),
    ('AZ_104',  'Microsoft Azure Administrator',                              NULL,         '☁️', 81),
    ('GCP_ACE', 'Google Cloud Associate Cloud Engineer',                      NULL,         '☁️', 82)
ON CONFLICT (code) DO NOTHING;

-- ────────────────────────────────────────────────────────────
--  3. FK nueva en academy_resources (nullable durante backfill)
-- ────────────────────────────────────────────────────────────
ALTER TABLE academy_resources
    ADD COLUMN IF NOT EXISTS certification_id UUID
    REFERENCES certifications(id) ON DELETE RESTRICT;

-- ────────────────────────────────────────────────────────────
--  4. Backfill: mapear el enum viejo a la nueva FK
-- ────────────────────────────────────────────────────────────
UPDATE academy_resources ar
SET    certification_id = c.id
FROM   certifications c
WHERE  c.code = ar.certification::TEXT
  AND  ar.certification_id IS NULL;

-- ────────────────────────────────────────────────────────────
--  5. Safety check — si queda algo sin mapear, abortar
-- ────────────────────────────────────────────────────────────
DO $$
DECLARE
    unmapped INTEGER;
BEGIN
    SELECT COUNT(*) INTO unmapped
    FROM   academy_resources
    WHERE  certification_id IS NULL;

    IF unmapped > 0 THEN
        RAISE EXCEPTION
            'Migration aborted: % academy_resources row(s) could not be mapped '
            'to certifications. Inspect with: '
            'SELECT id, title, certification FROM academy_resources WHERE certification_id IS NULL;',
            unmapped;
    END IF;
END $$;

-- ────────────────────────────────────────────────────────────
--  6. Ahora sí, hacer el FK obligatorio y dropear lo viejo
-- ────────────────────────────────────────────────────────────
ALTER TABLE academy_resources ALTER COLUMN certification_id SET NOT NULL;

DROP INDEX IF EXISTS idx_academy_cert;
ALTER TABLE academy_resources DROP COLUMN IF EXISTS certification;

DROP TYPE IF EXISTS cert_name;

CREATE INDEX idx_academy_cert_id ON academy_resources (certification_id);

COMMIT;

-- ============================================================
--  Verificación (correr después del COMMIT)
-- ============================================================
-- SELECT c.code, c.display_name, COUNT(ar.id) AS resource_count
--   FROM certifications c
--   LEFT JOIN academy_resources ar ON ar.certification_id = c.id
--  GROUP BY c.id
--  ORDER BY c.display_order;
