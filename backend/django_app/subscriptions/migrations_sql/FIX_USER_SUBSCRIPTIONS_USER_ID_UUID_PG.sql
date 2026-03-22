-- =============================================================================
-- user_subscriptions.user_id → UUID (references users.uuid_id)
-- PostgreSQL does NOT allow subqueries inside ALTER COLUMN ... USING.
-- This script uses a temp column + UPDATE ... JOIN, then swap columns.
--
-- There is no Django migration for this fix (apply this SQL manually).
-- If django_migrations still lists subscriptions.0003_fix_user_subscriptions_user_id_uuid,
-- delete that row so migrate state matches the repo.
-- =============================================================================

BEGIN;

-- 1) Drop only the foreign key on user_id
DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT tc.constraint_name AS cname
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_schema = kcu.constraint_schema
     AND tc.constraint_name = kcu.constraint_name
    WHERE tc.table_schema = 'public'
      AND tc.table_name = 'user_subscriptions'
      AND tc.constraint_type = 'FOREIGN KEY'
      AND kcu.column_name = 'user_id'
  LOOP
    EXECUTE format('ALTER TABLE user_subscriptions DROP CONSTRAINT IF EXISTS %I', r.cname);
  END LOOP;
END $$;

-- 2) Convert via temp column (no subquery in USING)
DO $$
DECLARE
  dt text;
BEGIN
  SELECT c.data_type INTO dt
  FROM information_schema.columns c
  WHERE c.table_schema = 'public'
    AND c.table_name = 'user_subscriptions'
    AND c.column_name = 'user_id';

  IF dt IS NULL THEN
    RAISE EXCEPTION 'Column public.user_subscriptions.user_id not found';
  END IF;

  IF lower(dt) = 'uuid' THEN
    RAISE NOTICE 'user_subscriptions.user_id is already uuid; skipping column conversion';
    RETURN;
  END IF;

  -- Clean up from a failed partial run
  ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS user_id_new;

  ALTER TABLE user_subscriptions ADD COLUMN user_id_new uuid;

  -- Integer / numeric string user ids → users.uuid_id (bigint, int, or varchar digits)
  UPDATE user_subscriptions us
  SET user_id_new = u.uuid_id
  FROM users u
  WHERE us.user_id::text ~ '^[0-9]+$'
    AND u.id = us.user_id::bigint;

  -- UUID-as-text only: never run this on bigint (negative ids match !~ '^[0-9]+$' and bigint::uuid errors)
  IF lower(dt) IN ('character varying', 'text', 'character') THEN
    UPDATE user_subscriptions us
    SET user_id_new = trim(us.user_id::text)::uuid
    WHERE us.user_id_new IS NULL
      AND us.user_id IS NOT NULL
      AND trim(us.user_id::text) !~ '^[0-9]+$';
  END IF;

  IF EXISTS (
    SELECT 1 FROM user_subscriptions
    WHERE user_id IS NOT NULL AND user_id_new IS NULL
  ) THEN
    RAISE EXCEPTION 'Unmapped user_id rows; fix orphans (no matching users.id) then retry';
  END IF;

  ALTER TABLE user_subscriptions DROP COLUMN user_id;
  ALTER TABLE user_subscriptions RENAME COLUMN user_id_new TO user_id;
  ALTER TABLE user_subscriptions ALTER COLUMN user_id SET NOT NULL;
END $$;

-- 3) OneToOne uniqueness (Django)
ALTER TABLE user_subscriptions DROP CONSTRAINT IF EXISTS user_subscriptions_user_id_key;
ALTER TABLE user_subscriptions
  ADD CONSTRAINT user_subscriptions_user_id_key UNIQUE (user_id);

-- 4) FK to users.uuid_id
ALTER TABLE user_subscriptions DROP CONSTRAINT IF EXISTS user_subscriptions_user_id_fkey;
ALTER TABLE user_subscriptions
  ADD CONSTRAINT user_subscriptions_user_id_fkey
  FOREIGN KEY (user_id)
  REFERENCES users (uuid_id)
  ON DELETE CASCADE;

-- 5) Restore composite index (matches Django 0002 name if you rely on it)
DROP INDEX IF EXISTS user_subscr_user_id_c57286_idx;
CREATE INDEX user_subscr_user_id_c57286_idx ON user_subscriptions (user_id, status);

COMMIT;

-- =============================================================================
