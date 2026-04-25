-- ============================================================
--  Migration 005 · Hotfix: karma trigger + backfill (originally 001 in patch v1.2)
--
--  Arregla el trigger que solo disparaba en INSERT (perdía los
--  cambios de voto y los UNDO) y recalcula karma_score desde
--  interactions para corregir los valores corruptos actuales.
--
--  Idempotente: se puede correr varias veces sin romper.
-- ============================================================

BEGIN;

-- ────────────────────────────────────────────────────────────
--  1. Reemplazar la función del trigger
--     Maneja: INSERT, UPDATE (cambio de voto), DELETE (undo)
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_karma_on_vote()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    article_author UUID;
    old_delta      INTEGER := 0;
    new_delta      INTEGER := 0;
BEGIN
    -- DELETE: reversar el voto antiguo
    IF TG_OP = 'DELETE' THEN
        SELECT author_id INTO article_author
        FROM   knowledge_base WHERE id = OLD.kb_id;

        IF article_author IS NOT NULL THEN
            old_delta := CASE WHEN OLD.vote = 'like' THEN 1 ELSE -1 END;
            UPDATE users
            SET    karma_score = karma_score - old_delta
            WHERE  id = article_author;
        END IF;
        RETURN OLD;
    END IF;

    -- INSERT o UPDATE: calcular el delta neto
    SELECT author_id INTO article_author
    FROM   knowledge_base WHERE id = NEW.kb_id;

    -- Autor borrado (author_id IS NULL por ON DELETE SET NULL) → no-op
    IF article_author IS NULL THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        old_delta := CASE WHEN OLD.vote = 'like' THEN 1 ELSE -1 END;
    END IF;

    new_delta := CASE WHEN NEW.vote = 'like' THEN 1 ELSE -1 END;

    -- Delta neto: (nuevo) - (viejo). En INSERT, old_delta=0 → delta = new_delta.
    UPDATE users
    SET    karma_score = karma_score + (new_delta - old_delta)
    WHERE  id = article_author;

    RETURN NEW;
END;
$$;

-- ────────────────────────────────────────────────────────────
--  2. Reattach trigger con los tres eventos
-- ────────────────────────────────────────────────────────────
DROP TRIGGER IF EXISTS trg_karma_on_vote ON interactions;

CREATE TRIGGER trg_karma_on_vote
    AFTER INSERT OR UPDATE OR DELETE ON interactions
    FOR EACH ROW EXECUTE FUNCTION update_karma_on_vote();

-- ────────────────────────────────────────────────────────────
--  3. Backfill · recalcular karma_score desde cero
--
--  El trigger viejo solo corría en INSERT, así que cualquier
--  usuario cuyo voto cambió o fue retirado tiene karma corrupto.
--  Reseteamos todos los karma y los re-derivamos de interactions.
-- ────────────────────────────────────────────────────────────
UPDATE users SET karma_score = 0;

UPDATE users u
SET    karma_score = sub.score
FROM (
    SELECT kb.author_id AS user_id,
           SUM(CASE WHEN i.vote = 'like' THEN 1 ELSE -1 END)::INTEGER AS score
    FROM   interactions  i
    JOIN   knowledge_base kb ON kb.id = i.kb_id
    WHERE  kb.author_id IS NOT NULL
    GROUP BY kb.author_id
) sub
WHERE  u.id = sub.user_id;

COMMIT;

-- ============================================================
--  Verificación · correr estas queries después del COMMIT
-- ============================================================

-- Top autores por karma
-- SELECT u.display_name, u.email, u.karma_score,
--        COUNT(DISTINCT kb.id) AS articles_authored
--   FROM users u
--   LEFT JOIN knowledge_base kb ON kb.author_id = u.id
--  GROUP BY u.id
--  ORDER BY u.karma_score DESC
--  LIMIT 20;

-- Sanity check: sumar karma vs. sumar interactions (deberían cuadrar)
-- SELECT
--     (SELECT SUM(karma_score) FROM users) AS total_karma,
--     (SELECT SUM(CASE WHEN i.vote='like' THEN 1 ELSE -1 END)
--        FROM interactions i
--        JOIN knowledge_base kb ON kb.id = i.kb_id
--       WHERE kb.author_id IS NOT NULL) AS expected_karma;
