-- ============================================================================
-- Fix: data_sources.auth_token encryption trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION encrypt_data_source_token()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.auth_token IS NOT NULL THEN
        IF pg_typeof(NEW.auth_token) IN ('text', 'varchar', 'bpchar', 'citext') THEN
            NEW.auth_token := pgp_sym_encrypt(NEW.auth_token::text, 'bedaanwaves_master_key');
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_encrypt_ds_token ON data_sources;

CREATE TRIGGER trg_encrypt_ds_token
    BEFORE INSERT OR UPDATE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION encrypt_data_source_token();

-- Create a view for decrypted access
CREATE OR REPLACE VIEW v_data_sources_decrypted AS
SELECT
    id,
    source_name,
    source_type,
    base_url,
    api_key_required,
    CASE
        WHEN auth_token IS NOT NULL
        THEN pgp_sym_decrypt(auth_token, 'bedaanwaves_master_key')::text
        ELSE NULL
    END AS auth_token,
    data_format,
    last_verification,
    verification_count,
    is_active,
    info,
    created_at,
    updated_at
FROM data_sources;

COMMENT ON VIEW v_data_sources_decrypted IS
    'View that transparently decrypts data_sources.auth_token. Use for read-only access by admin tools.';
