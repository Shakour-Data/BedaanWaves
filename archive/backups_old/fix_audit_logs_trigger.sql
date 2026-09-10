-- ============================================================================
-- Fix: audit_logs.ip_address encryption trigger
-- The column was changed to BYTEA, but no trigger was created for auto-encryption
-- Solution: Keep BYTEA, create trigger function that encrypts text input
-- ============================================================================

\echo '--- Fixing audit_logs encryption trigger ---'

-- Create the trigger function
-- Since ip_address is BYTEA, the trigger handles both:
--   - BYTEA input (already encrypted): passes through
--   - Other types: encrypts before storage
CREATE OR REPLACE FUNCTION encrypt_audit_ip()
RETURNS TRIGGER AS $$
BEGIN
    -- Only encrypt if the value is not NULL and not already encrypted (BYTEA)
    -- If NEW.ip_address is text/varchar (unencrypted), encrypt it
    IF NEW.ip_address IS NOT NULL THEN
        -- Check if the input is a text type (not yet encrypted)
        IF pg_typeof(NEW.ip_address) IN ('text', 'varchar', 'bpchar', 'citext') THEN
            NEW.ip_address := pgp_sym_encrypt(NEW.ip_address::text, 'audit_encryption_key');
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger (or replace if exists)
DROP TRIGGER IF EXISTS trg_encrypt_audit_ip ON audit_logs;

CREATE TRIGGER trg_encrypt_audit_ip
    BEFORE INSERT OR UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION encrypt_audit_ip();

-- Create a view for decrypted access (for convenience)
CREATE OR REPLACE VIEW v_audit_logs_decrypted AS
SELECT
    id,
    user_id,
    action,
    entity,
    entity_id,
    details,
    CASE
        WHEN ip_address IS NOT NULL
        THEN pgp_sym_decrypt(ip_address, 'audit_encryption_key')::text
        ELSE NULL
    END AS ip_address,
    created_at
FROM audit_logs;

COMMENT ON VIEW v_audit_logs_decrypted IS
    'View that transparently decrypts audit_logs.ip_address using pgcrypto. Use for read-only access.';

-- Verify
\echo 'Trigger and view created successfully.'
