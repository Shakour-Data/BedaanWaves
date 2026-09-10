-- ============================================================================
-- FINAL COMPREHENSIVE VERIFICATION
-- ============================================================================

\echo '=== FINAL COMPREHENSIVE VERIFICATION ==='
\echo ''

-- 1. Assets: only NASDAQ EQUITY and ETF
\echo '--- 1. Assets Verification ---'
SELECT
    count(*) AS total_assets,
    count(*) FILTER (WHERE market = 'NASDAQ') AS nasdaq_assets,
    count(*) FILTER (WHERE currency = 'USD') AS usd_assets,
    count(*) FILTER (WHERE currency = 'IRR') AS irr_assets,
    count(*) FILTER (WHERE asset_class = 'EQUITY') AS equity_count,
    count(*) FILTER (WHERE asset_class = 'ETF') AS etf_count
FROM assets;

-- Verify ^IXIC exists as EQUITY
\echo ''
SELECT symbol, name, asset_class, market FROM assets WHERE symbol = '^IXIC';

-- Verify no non-NASDAQ assets
\echo ''
\echo 'Non-NASDAQ assets (should be 0):'
SELECT count(*) FROM assets WHERE market != 'NASDAQ' OR asset_class NOT IN ('EQUITY', 'ETF');

-- 2. Table count
\echo ''
\echo '--- 2. Table Count ---'
SELECT count(*) AS total_tables FROM pg_tables WHERE schemaname = 'public';

-- 3. No IR/crypto tables
\echo ''
\echo '--- 3. IR/Crypto Tables (should be 0) ---'
SELECT count(*) AS ir_tables FROM pg_tables WHERE tablename LIKE 'ir_%';
SELECT count(*) AS crypto_tables FROM pg_tables WHERE tablename LIKE 'crypto_%';

-- 4. FK constraints with CASCADE
\echo ''
\echo '--- 4. FK Constraints with ON DELETE CASCADE ---'
SELECT conname, confrelid::regclass as referenced
FROM pg_constraint
WHERE contype = 'f' AND confdeltype = 'c'
  AND conrelid::regclass::text IN ('positions','watchlist_items','news_sentiment','screening_results')
ORDER BY conname;

-- 5. FK with SET NULL
\echo ''
\echo '--- 5. FK with ON DELETE SET NULL ---'
SELECT conname, confrelid::regclass as referenced
FROM pg_constraint
WHERE contype = 'f' AND confdeltype = 'n'
  AND conrelid::regclass::text = 'api_logs';

-- 6. GIN Indexes
\echo ''
\echo '--- 6. GIN Indexes ---'
SELECT count(*) AS gin_index_count FROM pg_indexes WHERE indexdef ILIKE '%gin%' AND schemaname='public';

-- 7. BRIN Indexes
\echo ''
\echo '--- 7. BRIN Indexes ---'
SELECT tablename, indexname FROM pg_indexes WHERE indexdef ILIKE '%brin%' AND schemaname='public' ORDER BY tablename;

-- 8. Partitioned tables
\echo ''
\echo '--- 8. Partitioned Tables ---'
SELECT relname as table_name, count(*) as partition_count
FROM pg_class c
JOIN pg_inherits i ON i.inhparent = c.oid
WHERE c.relkind = 'p' AND c.relnamespace = 'public'::regnamespace
GROUP BY c.relname;

-- 9. intl_price_candles verification
\echo ''
\echo '--- 9. intl_price_candles Verification ---'
SELECT
    count(*) as total_rows,
    min(timestamp) as min_ts,
    max(timestamp) as max_ts
FROM intl_price_candles;

-- 10. Materialized Views
\echo ''
\echo '--- 10. Materialized Views ---'
SELECT matviewname, ispopulated FROM pg_matviews WHERE schemaname = 'public';

-- 11. Views
\echo ''
\echo '--- 11. All Views ---'
SELECT viewname FROM pg_views WHERE schemaname = 'public' ORDER BY viewname;

-- 12. Encrypted columns
\echo ''
\echo '--- 12. Encrypted Columns ---'
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name IN ('auth_token', 'ip_address')
  AND data_type = 'bytea'
  AND table_name NOT LIKE 'v_%'
ORDER BY table_name;

-- 13. Encryption triggers
\echo ''
\echo '--- 13. Encryption Triggers ---'
SELECT tgname FROM pg_trigger WHERE tgname LIKE '%encrypt%' AND tgenabled = 'O';

-- 14. Database roles
\echo ''
\echo '--- 14. Database Roles ---'
SELECT rolname FROM pg_roles WHERE rolname LIKE 'bedaan%' ORDER BY rolname;

-- 15. Database extensions
\echo ''
\echo '--- 15. Extensions ---'
SELECT extname, extversion FROM pg_extension ORDER BY extname;

-- 16. COMMENT coverage
\echo ''
\echo '--- 16. Tables with Comments ---'
SELECT count(*) AS tables_with_comments
FROM pg_class c
WHERE c.relkind = 'r'
  AND c.relnamespace = 'public'::regnamespace
  AND obj_description(c.oid) IS NOT NULL;

-- 17. CHECK constraints on assets
\echo ''
\echo '--- 17. Assets CHECK Constraints ---'
SELECT conname, pg_get_constraintdef(c.oid)
FROM pg_constraint c
WHERE c.conrelid = 'assets'::regclass AND c.contype = 'c';

-- 18. Autovacuum settings on top 5 tables
\echo ''
echo '--- 18. Autovacuum Settings (sample) ---'
SELECT c.relname, c.reloptions
FROM pg_class c
WHERE c.relname IN ('intl_price_candles','market_data_snapshots','raw_market_data','api_logs','score_history','ml_signals')
  AND c.relkind = 'r'
  AND c.relnamespace = 'public'::regnamespace
  AND c.reloptions IS NOT NULL
ORDER BY c.relname;

-- 19. No orphaned data
\echo ''
echo '--- 19. Orphan Check (should all be 0) ---'
SELECT 'ml_signals' as tbl, count(*) as orphans FROM ml_signals WHERE asset_id NOT IN (SELECT id FROM assets)
UNION ALL SELECT 'positions', count(*) FROM positions WHERE asset_id NOT IN (SELECT id FROM assets)
UNION ALL SELECT 'score_history', count(*) FROM score_history WHERE asset_id NOT IN (SELECT id FROM assets)
UNION ALL SELECT 'market_data_snapshots', count(*) FROM market_data_snapshots WHERE asset_id NOT IN (SELECT id FROM assets)
UNION ALL SELECT 'alerts', count(*) FROM alerts WHERE asset_id NOT IN (SELECT id FROM assets)
UNION ALL SELECT 'scoring_snapshots', count(*) FROM scoring_snapshots WHERE asset_id NOT IN (SELECT id FROM assets);

-- 20. Sample EXPLAIN to verify partition pruning works
\echo ''
echo '--- 20. Partition Pruning EXPLAIN ---'
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
SELECT count(*) FROM intl_price_candles
WHERE timestamp >= '2025-01-01' AND timestamp < '2025-04-01';

\echo ''
\echo '=== FINAL VERIFICATION COMPLETE ==='
