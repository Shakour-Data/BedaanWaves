-- ============================================================================
-- Comprehensive Verification of All Migration Changes
-- ============================================================================

\echo '=== COMPREHENSIVE VERIFICATION ==='
\echo ''

-- 1. FK Constraints with ON DELETE CASCADE
\echo '--- 1. FK Constraints (ON DELETE CASCADE) ---'
SELECT conname, confrelid::regclass as referenced_table, confdeltype
FROM pg_constraint
WHERE contype = 'f'
  AND conrelid::regclass::text IN ('positions','watchlist_items','news_sentiment','screening_results')
ORDER BY conrelid::regclass::text, conname;

-- 2. FK on api_logs
\echo ''
\echo '--- 2. FK on api_logs.user_id ---'
SELECT conname, confrelid::regclass as referenced_table, confdeltype
FROM pg_constraint
WHERE contype = 'f' AND conrelid = 'api_logs'::regclass;

-- 3. GIN Indexes
\echo ''
\echo '--- 3. GIN Indexes on JSONB Columns ---'
SELECT tablename, indexname
FROM pg_indexes
WHERE indexdef LIKE '%USING GIN%'
  AND schemaname = 'public'
ORDER BY tablename, indexname;

-- 4. BRIN Indexes
\echo ''
\echo '--- 4. BRIN Indexes ---'
SELECT tablename, indexname
FROM pg_indexes
WHERE indexdef LIKE '%USING BRIN%'
  AND schemaname = 'public'
ORDER BY tablename, indexname;

-- 5. Encrypted columns
\echo ''
\echo '--- 5. Encrypted Columns (pgcrypto) ---'
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE column_name IN ('auth_token', 'ip_address')
  AND table_schema = 'public'
ORDER BY table_name;

-- 6. Triggers for encryption
\echo ''
\echo '--- 6. Encryption Triggers ---'
SELECT tgname, tgenabled
FROM pg_trigger
WHERE tgname LIKE '%encrypt%' AND tgenabled = 'O'
ORDER BY tgname;

-- 7. Partitioned tables
\echo ''
\echo '--- 7. Partitioned Tables ---'
SELECT c.relname as parent_table, count(p.inhrelid) as partition_count
FROM pg_class c
JOIN pg_partition p ON p.partrelid = c.oid
WHERE c.relkind = 'p'
  AND c.relnamespace = 'public'::regnamespace
GROUP BY c.relname
ORDER BY c.relname;

-- 8. intl_price_candles partitions
\echo ''
\echo '--- 8. intl_price_candles Partitions ---'
SELECT inhrelid::regclass as partition_name,
       (SELECT count(*) FROM inhrelid::regclass) as row_count
FROM pg_inherits
WHERE inhparent = 'intl_price_candles'::regclass
  AND inhrelid::regclass::text NOT LIKE '%default%'
ORDER BY partition_name;

-- Also show default partition
\echo ''
\echo '--- 8b. Default partition row count ---'
SELECT 'intl_price_candles_default' as partition_name,
       (SELECT count(*) FROM intl_price_candles_default) as row_count;

-- 9. Total row count in partitioned table
\echo ''
\echo '--- 9. Total rows in partitioned intl_price_candles ---'
SELECT count(*) as total_rows FROM intl_price_candles;

-- 10. Materialized Views
\echo ''
\echo '--- 10. Materialized Views ---'
SELECT matviewname, ispopulated,
       (SELECT count(*) FROM mv_daily_score_trends) as mv_scores_rows
FROM pg_matviews
WHERE schemaname = 'public';

-- 11. Database Roles
\echo ''
\echo '--- 11. Database Roles ---'
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname LIKE 'bedaan%'
ORDER BY rolname;

-- 12. Autovacuum settings on key tables
\echo ''
\echo '--- 12. Autovacuum Settings on Large Tables ---'
SELECT relname,
       reloptions->>'autovacuum_vacuum_scale_factor' as vacuum_scale,
       reloptions->>'autovacuum_analyze_scale_factor' as analyze_scale
FROM pg_class c
JOIN (
    SELECT oid, unnest(reloptions) as reloption
    FROM pg_class WHERE reloptions IS NOT NULL
) r ON r.oid = c.oid
WHERE relname IN ('intl_price_candles','market_data_snapshots','raw_market_data','api_logs','score_history')
  AND reloption LIKE 'autovacuum%'
ORDER BY relname;

-- 13. COMMENT coverage
\echo ''
\echo '--- 13. Tables with Comments ---'
SELECT obj_description(c.oid) as table_comment, c.relname as table_name
FROM pg_class c
WHERE c.relkind = 'r' AND c.relnamespace = 'public'::regnamespace
  AND obj_description(c.oid) IS NOT NULL
ORDER BY c.relname;

-- 14. Database extensions
\echo ''
\echo '--- 14. Database Extensions ---'
SELECT extname, extversion FROM pg_extension ORDER BY extname;

-- 15. Verify macro_forecasts table and constraint
\echo ''
\echo '--- 15. Macro Forecasts Table ---'
SELECT tablename FROM pg_tables WHERE tablename = 'macro_forecasts';
SELECT conname FROM pg_constraint WHERE conrelid = 'macro_indicators'::regclass AND contype = 'u';

-- 16. CHECK constraints on assets
\echo ''
\echo '--- 16. Assets CHECK Constraints ---'
SELECT conname, pg_get_constraintdef(c.oid)
FROM pg_constraint c
WHERE c.conrelid = 'assets'::regclass
  AND c.contype = 'c';

-- 17. Position valuation view
\echo ''
\echo '--- 17. Views ---'
SELECT viewname FROM pg_views WHERE schemaname = 'public' AND viewname LIKE '%valuat%' OR viewname LIKE '%decrypted%' OR viewname LIKE '%portfolio_perf%';

-- 18. Column comments
\echo ''
\echo '--- 18. Sample Column Comments ---'
SELECT col_description(c.oid, a.attnum) as col_comment,
       c.relname as table_name, a.attname as column_name
FROM pg_class c
JOIN pg_attribute a ON a.attrelid = c.oid
WHERE c.relnamespace = 'public'::regnamespace
  AND c.relkind = 'r'
  AND col_description(c.oid, a.attnum) IS NOT NULL
  AND c.relname IN ('intl_price_candles', 'assets', 'audit_logs', 'data_sources')
ORDER BY c.relname, a.attnum;

\echo ''
\echo '=== VERIFICATION COMPLETE ==='
