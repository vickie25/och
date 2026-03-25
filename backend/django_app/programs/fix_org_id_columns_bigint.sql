-- =============================================================================
-- Fix org_id type mismatch: PostgreSQL error
--   operator does not exist: uuid = integer
--   ... SET "org_id" = NULL WHERE "waitlist"."org_id" IN (6)
--
-- Django expects Organization.id as BIGINT (BigAutoField). If waitlist.org_id
-- or enrollments.org_id are UUID (or other wrong type), DELETE on organizations
-- fails when SET_NULL runs.
--
-- For each table: if org_id exists and is not bigint, drop and recreate as
-- BIGINT FK. Existing org_id values are lost for that column when recreated.
-- Tables that already have bigint org_id are left unchanged.
--
-- Run: psql "$DATABASE_URL" -f fix_org_id_columns_bigint.sql
-- =============================================================================

BEGIN;

CREATE OR REPLACE FUNCTION _drop_fk_on_column(p_table text, p_col text)
RETURNS void AS $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT tc.constraint_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_schema = kcu.constraint_schema
     AND tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    WHERE tc.table_schema = current_schema()
      AND tc.table_name = p_table
      AND kcu.column_name = p_col
      AND tc.constraint_type = 'FOREIGN KEY'
  LOOP
    EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', p_table, r.constraint_name);
  END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION _ensure_org_id_bigint(p_table text)
RETURNS void AS $$
DECLARE
  dt text;
BEGIN
  SELECT c.data_type INTO dt
  FROM information_schema.columns c
  WHERE c.table_schema = current_schema()
    AND c.table_name = p_table
    AND c.column_name = 'org_id';

  IF dt IS NULL THEN
    EXECUTE format(
      'ALTER TABLE %I ADD COLUMN org_id BIGINT NULL REFERENCES organizations(id) ON DELETE SET NULL',
      p_table
    );
    RETURN;
  END IF;

  -- Already compatible with organizations.id (bigint)
  IF dt IN ('bigint', 'integer', 'smallint') THEN
    RETURN;
  END IF;

  PERFORM _drop_fk_on_column(p_table, 'org_id');
  EXECUTE format('ALTER TABLE %I DROP COLUMN org_id', p_table);
  EXECUTE format(
    'ALTER TABLE %I ADD COLUMN org_id BIGINT NULL REFERENCES organizations(id) ON DELETE SET NULL',
    p_table
  );
END;
$$ LANGUAGE plpgsql;

SELECT _ensure_org_id_bigint('waitlist');
SELECT _ensure_org_id_bigint('enrollments');

DROP FUNCTION _ensure_org_id_bigint(text);
DROP FUNCTION _drop_fk_on_column(text, text);

COMMIT;
