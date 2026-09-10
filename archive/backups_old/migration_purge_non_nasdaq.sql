-- ============================================================================
-- BedaanWaves PostgreSQL Purge Migration — Nasdaq-Only Enforcement
-- ============================================================================
-- This migration purges ALL non-NASDAQ financial instruments:
--   - Iranian stocks (TSE market, IRR currency): 5 assets
--   - Cryptocurrencies (CRYPTO class, GLOBAL market): 10 assets
--   - All IR-specific tables and their data
--   - All crypto-specific tables and their data
--   - Dependent data in shared tables (ml_signals, score_history, etc.)
--
-- The ^IXIC (Nasdaq Composite) reference row is kept but reclassified as EQUITY.
-- ============================================================================

\echo '=== Nasdaq-Only Purge: Starting ==='

-- ============================================================================
-- Step 1: Update ^IXIC to asset_class='EQUITY' BEFORE purge
-- (Otherwise the purge query would delete it too)
-- ============================================================================

\echo '--- Updating ^IXIC asset_class to EQUITY ---'
UPDATE assets
    SET asset_class = 'EQUITY'
    WHERE symbol = '^IXIC' AND asset_class = 'INDEX';

-- ============================================================================
-- Step 2: Collect non-NASDAQ asset IDs for logging
-- ============================================================================

\echo '--- Identifying non-NASDAQ assets to purge ---'

CREATE TEMP TABLE non_nasdaq_assets AS
SELECT id, symbol, name, asset_class, market, currency
FROM assets
WHERE market != 'NASDAQ' OR asset_class NOT IN ('EQUITY', 'ETF');

SELECT count(*) AS non_nasdaq_count FROM non_nasdaq_assets;

-- ============================================================================
-- Step 3: Purge dependent data from shared tables
--    (Delete rows referencing non-NASDAQ asset IDs)
-- ============================================================================

\echo '--- Deleting dependent data from shared tables ---'

-- Tables with FK to assets.id (excluding those already CASCADE-deleted)
-- Order: child tables first, then parent

-- ml_signals
DELETE FROM ml_signals
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from ml_signals'

-- ml_predictions (references ml_models, not assets directly — but has asset_id)
DELETE FROM ml_predictions
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from ml_predictions'

-- score_history
DELETE FROM score_history
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from score_history'

-- scoring_snapshots
DELETE FROM scoring_snapshots
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from scoring_snapshots'

-- raw_performance_scores
DELETE FROM raw_performance_scores
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from raw_performance_scores'

-- processed_feature_data
DELETE FROM processed_feature_data
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from processed_feature_data'

-- fundamental_ratios
DELETE FROM fundamental_ratios
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from fundamental_ratios'

-- financial_statements
DELETE FROM financial_statements
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from financial_statements'

-- market_data_snapshots
DELETE FROM market_data_snapshots
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from market_data_snapshots'

-- raw_market_data
DELETE FROM raw_market_data
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from raw_market_data'

-- news (FK to assets)
DELETE FROM news
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from news'

-- news_sentiment (FK to assets and news)
DELETE FROM news_sentiment
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from news_sentiment'

-- anomalies
DELETE FROM anomalies
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from anomalies'

-- alerts
DELETE FROM alerts
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from alerts'

-- company_leadership
DELETE FROM company_leadership
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from company_leadership'

-- screening_results (no asset_id FK, but user_id — keep these)

-- user_scoring_results (no asset_id, uses symbol string — clean separately)
DELETE FROM user_scoring_results
    WHERE symbol IN (SELECT symbol FROM non_nasdaq_assets);

-- corporate_events
DELETE FROM corporate_events
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from corporate_events'

-- watchlist_items (ON DELETE CASCADE handles portfolios/watchlists, but asset FK stays)
DELETE FROM watchlist_items
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from watchlist_items'

-- user_favorites (uses symbol string)
DELETE FROM user_favorites
    WHERE symbol IN (SELECT symbol FROM non_nasdaq_assets);
\echo 'Deleted from user_favorites'

-- user_alerts (uses symbol string)
DELETE FROM user_alerts
    WHERE symbol IN (SELECT symbol FROM non_nasdaq_assets);
\echo 'Deleted from user_alerts'

-- coefficient_adjustments
DELETE FROM coefficient_adjustments
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from coefficient_adjustments'

-- coefficient_history
DELETE FROM coefficient_history
    WHERE asset_id IN (SELECT id FROM non_nasdaq_assets);
\echo 'Deleted from coefficient_history'

-- ============================================================================
-- Step 4: Drop IR-specific tables (all empty)
-- ============================================================================

\echo '--- Dropping IR-specific tables ---'
DROP TABLE IF EXISTS ir_price_candles CASCADE;
DROP TABLE IF EXISTS ir_order_book CASCADE;
DROP TABLE IF EXISTS ir_free_float CASCADE;
DROP TABLE IF EXISTS ir_major_shareholders CASCADE;
DROP TABLE IF EXISTS ir_retail_institutional CASCADE;

-- ============================================================================
-- Step 5: Purge data from and drop crypto-specific tables
-- ============================================================================

\echo '--- Purging crypto data and dropping crypto tables ---'

-- Truncate crypto tables with data
TRUNCATE TABLE crypto_price_candles, crypto_order_book, crypto_ml_signals, cryptocurrencies;

DROP TABLE IF EXISTS crypto_price_candles CASCADE;
DROP TABLE IF EXISTS crypto_order_book CASCADE;
DROP TABLE IF EXISTS crypto_ml_signals CASCADE;
DROP TABLE IF EXISTS cryptocurrencies CASCADE;
DROP TABLE IF EXISTS user_crypto_configs CASCADE;
DROP TABLE IF EXISTS user_crypto_settings CASCADE;

-- ============================================================================
-- Step 6: Delete non-NASdaqM assets from the assets table
-- ============================================================================

\echo '--- Deleting non-NASDAQ assets from assets table ---'
DELETE FROM assets
    WHERE id IN (SELECT id FROM non_nasdaq_assets);

-- ============================================================================
-- Step 7: Add CHECK constraints to enforce NASDAQ-only
-- ============================================================================

\echo '--- Adding NASDAQ-only CHECK constraints ---'

-- DROP the temp table is not needed (auto-cleaned)

-- Remove the old chk_assets_currency_valid and re-add without IRR
ALTER TABLE assets DROP CONSTRAINT IF EXISTS chk_assets_currency_valid;
ALTER TABLE assets ADD CONSTRAINT chk_assets_currency_valid
    CHECK (currency IN ('USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'CHF', 'AUD', 'INR', 'KRW'));

-- Add CHECK for market = NASDAQ only
ALTER TABLE assets ADD CONSTRAINT chk_assets_market
    CHECK (market = 'NASDAQ');

-- Add CHECK for asset_class = EQUITY or ETF only
ALTER TABLE assets ADD CONSTRAINT chk_assets_asset_class
    CHECK (asset_class IN ('EQUITY', 'ETF'));

-- ============================================================================
-- Step 8: Verify purge results
-- ============================================================================

\echo '--- Purge verification ---'
SELECT count(*) AS remaining_assets FROM assets;
SELECT count(*) AS ir_or_crypto_assets FROM assets WHERE market != 'NASDAQ';
SELECT count(*) AS non_equity_etf_assets FROM assets WHERE asset_class NOT IN ('EQUITY', 'ETF');
SELECT count(*) AS irr_assets FROM assets WHERE currency = 'IRR';

-- Check that ^IXIC survived
SELECT symbol, name, asset_class, market FROM assets WHERE symbol = '^IXIC';

-- Check IR/crypto tables are gone
SELECT count(*) AS ir_tables_remaining FROM pg_tables WHERE tablename LIKE 'ir_%';
SELECT count(*) AS crypto_tables_remaining FROM pg_tables WHERE tablename LIKE 'crypto_%';

-- Check no dependent data references non-NASDAQ assets
SELECT count(*) AS orphaned_ml_signals FROM ml_signals WHERE asset_id NOT IN (SELECT id FROM assets);
SELECT count(*) AS orphaned_score_history FROM score_history WHERE asset_id NOT IN (SELECT id FROM assets);
SELECT count(*) AS orphaned_ml_predictions FROM ml_predictions WHERE asset_id NOT IN (SELECT id FROM assets);
SELECT count(*) AS orphaned_positions FROM positions WHERE asset_id NOT IN (SELECT id FROM assets);

-- ============================================================================
-- Step 9: Add COMMENT for the purge
-- ============================================================================

COMMENT ON TABLE assets IS 'Core asset/symbol master data. ONLY NASDAQ-listed EQUITY and ETF instruments stored. Non-NASDAQ purged. ^IXIC (Nasdaq Composite) kept as reference.';

-- ============================================================================
-- Clean up
-- ============================================================================
DROP TABLE non_nasdaq_assets;

\echo '=== Nasdaq-Only Purge: Complete ==='
