-- =====================================================================
-- BedaänWaves — Database Purification Script (FULL Nasdaq exchange scope)
-- =====================================================================
-- Scope:  This database is exclusively for instruments that trade on the
--         Nasdaq Stock Market. That means:
--           (1) Every row in `assets` with market = 'NASDAQ' (any
--               EQUITY / ETF / etc. that lists on Nasdaq — roughly
--               3,500+ tickers).
--           (2) The Nasdaq Composite reference index, ^IXIC.
--           (3) The Invesco QQQ ETF (which already lists on Nasdaq).
--
--         Everything else is purged:
--           * Non-Nasdaq equities (NYSE, AMEX, OTC, BINANCE, ...)
--           * Non-Nasdaq indices (^GSPC S&P 500, ^DJI Dow, ^RUT Russell,
--             ^FTSE, ^GDAXI, ^N225, ^HSI, ^VIX, ^TNX, ...)
--           * Crypto, forex, commodities, futures (BTC-USD, ETHUSDT,
--             GC=F, CL=F, EURUSD, ...)
--           * Non-Nasdaq sector ETFs (XLK, XLF, XLE, ...) which trade
--             on NYSE Arca even though some are tagged 'NASDAQ' in
--             feeds.
--
-- Action: DELETE rows that violate scope. Tables are preserved (no
--         DROP TABLE). Foreign keys are handled by temporarily attaching
--         ON DELETE CASCADE so DELETE FROM assets cannot be blocked by
--         orphaned child rows. Users are preserved.
--
-- Run:    psql -U postgres -d bedaanwaves_db -v ON_ERROR_STOP=1 \
--             -f purification/purify_to_nasdaq.sql
-- =====================================================================

\set ON_ERROR_STOP on
BEGIN;

-- ---------------------------------------------------------------------
-- 0. Hard-deny list
--    These tickers are explicitly forbidden even if their `market`
--    column happens to say NASDAQ. They are non-Nasdaq indices,
--    sector ETFs traded on NYSE Arca, futures, crypto, and forex
--    pairs that commonly appear in yfinance feeds.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE forbidden (symbol TEXT PRIMARY KEY);
INSERT INTO forbidden (symbol) VALUES
    -- Non-Nasdaq US equity indices
    ('^GSPC'), ('^DJI'),  ('^RUT'),  ('^VIX'),  ('^TNX'),
    ('^SPX'), ('^SPC'),  ('SPX'),   ('DJIA'),  ('DJI'),
    -- International indices
    ('^FTSE'), ('^GDAXI'), ('^N225'), ('^HSI'),
    -- Sector & asset-class ETFs that trade on NYSE Arca
    ('XLK'),  ('XLV'),   ('XLF'),   ('XLE'),   ('XLB'),
    ('XLI'),  ('XLY'),   ('XLP'),   ('XLU'),
    ('XLE'),  ('SPY'),   ('VOO'),   ('IVV'),
    ('TLT'),  ('HYG'),   ('GLD'),   ('SLV'),
    ('EEM'),  ('VWO'),   ('IWM'),
    -- Futures & commodities
    ('GC=F'), ('CL=F'),  ('SI=F'),  ('NG=F'),
    -- Forex (kept here as a hard-deny so they can never reappear)
    ('EURUSD'), ('USDJPY'), ('GBPUSD'), ('USDEUR'), ('USDGBP');
DELETE FROM forbidden a USING forbidden b
 WHERE a.ctid > b.ctid AND a.symbol = b.symbol;

-- ---------------------------------------------------------------------
-- 1. Ensure ^IXIC and QQQ reference rows exist
-- ---------------------------------------------------------------------
INSERT INTO assets (symbol, name, asset_class, market, country_code, currency, active)
VALUES
    ('^IXIC', 'Nasdaq Composite',  'INDEX', 'NASDAQ', 'US', 'USD', TRUE),
    ('QQQ',   'Invesco QQQ Trust', 'ETF',   'NASDAQ', 'US', 'USD', TRUE)
ON CONFLICT (symbol) DO UPDATE
   SET asset_class = 'ETF',
       market      = 'NASDAQ',
       active      = TRUE
 WHERE assets.symbol = EXCLUDED.symbol;

-- ^IXIC must stay INDEX
UPDATE assets SET asset_class = 'INDEX'
 WHERE symbol = '^IXIC';

-- ---------------------------------------------------------------------
-- 2. Detach + reattach child FKs with ON DELETE CASCADE
--    (No DROP TABLE, only constraint swap.)
-- ---------------------------------------------------------------------
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN
        SELECT con.conname, con.conrelid::regclass AS tbl
          FROM pg_constraint con
          JOIN pg_class c ON c.oid = con.conrelid
         WHERE con.contype = 'f'
           AND pg_get_constraintdef(con.oid) ILIKE '%REFERENCES assets%'
           AND c.relname IN (
                'price_candles','intl_price_candles','ml_signals',
                'financial_statements','fundamental_ratios',
                'company_leadership','alerts','news',
                'positions','watchlist_items','symbols',
                'technical_indicators'
           )
           AND NOT con.confdeltype IN ('c','a')
    LOOP
        EXECUTE format(
            'ALTER TABLE %s DROP CONSTRAINT %I, '
            'ADD CONSTRAINT %I FOREIGN KEY (asset_id) REFERENCES assets(id) '
            'ON DELETE CASCADE',
            r.tbl, r.conname, r.conname
        );
        RAISE NOTICE 'Cascade added to %.%', r.tbl, r.conname;
    END LOOP;
END $$;

-- ---------------------------------------------------------------------
-- 3. Purge user-linked tables that store symbols directly
-- ---------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'user_favorites') THEN
        EXECUTE $f$
            DELETE FROM user_favorites
             WHERE UPPER(symbol) IN (SELECT UPPER(symbol) FROM forbidden)
                OR market IS DISTINCT FROM 'NASDAQ'
        $f$;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'user_alerts') THEN
        EXECUTE $f$
            DELETE FROM user_alerts
             WHERE UPPER(symbol) IN (SELECT UPPER(symbol) FROM forbidden)
                OR market IS DISTINCT FROM 'NASDAQ'
        $f$;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'alerts') THEN
        EXECUTE $f$
            DELETE FROM alerts
             WHERE UPPER(symbol) IN (SELECT UPPER(symbol) FROM forbidden)
                OR market IS DISTINCT FROM 'NASDAQ'
        $f$;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'watchlist_items') THEN
        EXECUTE $f$
            DELETE FROM watchlist_items
             WHERE UPPER(symbol) IN (SELECT UPPER(symbol) FROM forbidden)
                OR market IS DISTINCT FROM 'NASDAQ'
        $f$;
    END IF;
END $$;

-- ---------------------------------------------------------------------
-- 4. The big purge
--    A row is purged if EITHER:
--      (a) assets.market <> 'NASDAQ' (i.e. it lists on a different
--          exchange — NYSE, AMEX, OTC, BINANCE, FOREX, CRYPTO, ...), OR
--      (b) assets.symbol is in the hard-deny list (non-Nasdaq indices
--          and NYSE-Arca ETFs that some feeds tag 'NASDAQ' incorrectly).
-- ---------------------------------------------------------------------
DELETE FROM assets a
 USING forbidden f
 WHERE UPPER(a.symbol) = UPPER(f.symbol);

DELETE FROM assets
 WHERE market IS DISTINCT FROM 'NASDAQ'
   AND symbol NOT IN ('^IXIC', 'QQQ');   -- belt-and-braces

-- ---------------------------------------------------------------------
-- 5. Lock the schema so future drift cannot re-introduce offenders
-- ---------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='assets' AND column_name='market') THEN
        BEGIN
            ALTER TABLE assets
              ADD CONSTRAINT chk_assets_market_nasdaq_only
              CHECK (market = 'NASDAQ');
        EXCEPTION WHEN duplicate_object THEN
            ALTER TABLE assets DROP CONSTRAINT chk_assets_market_nasdaq_only;
            ALTER TABLE assets
              ADD CONSTRAINT chk_assets_market_nasdaq_only
              CHECK (market = 'NASDAQ');
        END;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='assets' AND column_name='asset_class') THEN
        BEGIN
            ALTER TABLE assets
              ADD CONSTRAINT chk_assets_asset_class_nasdaq_only
              CHECK (asset_class IN ('EQUITY','ETF','INDEX','ADR','RIGHT','WARRANT','UNIT'));
        EXCEPTION WHEN duplicate_object THEN
            ALTER TABLE assets DROP CONSTRAINT chk_assets_asset_class_nasdaq_only;
            ALTER TABLE assets
              ADD CONSTRAINT chk_assets_asset_class_nasdaq_only
              CHECK (asset_class IN ('EQUITY','ETF','INDEX','ADR','RIGHT','WARRANT','UNIT'));
        END;
    END IF;
END $$;

-- ---------------------------------------------------------------------
-- 6. Post-purge assertions (rollback on any failure)
-- ---------------------------------------------------------------------
DO $$
DECLARE
    total      INT;
    non_nasdaq INT;
    forbidden_left INT;
    has_qqq    INT;
    has_ixic   INT;
BEGIN
    SELECT COUNT(*) INTO total          FROM assets;
    SELECT COUNT(*) INTO non_nasdaq     FROM assets WHERE market <> 'NASDAQ';
    SELECT COUNT(*) INTO forbidden_left FROM assets a
      JOIN forbidden f ON UPPER(a.symbol) = UPPER(f.symbol);
    SELECT COUNT(*) INTO has_qqq  FROM assets WHERE symbol = 'QQQ';
    SELECT COUNT(*) INTO has_ixic FROM assets WHERE symbol = '^IXIC';

    RAISE NOTICE 'Post-purge rows: %', total;
    RAISE NOTICE '  QQQ present: %, ^IXIC present: %', has_qqq, has_ixic;
    RAISE NOTICE '  Non-NASDAQ rows remaining: %', non_nasdaq;
    RAISE NOTICE '  Hard-deny rows remaining: %', forbidden_left;

    IF non_nasdaq <> 0 THEN
        RAISE EXCEPTION 'Purge failed: % non-NASDAQ rows remain', non_nasdaq;
    END IF;
    IF forbidden_left <> 0 THEN
        RAISE EXCEPTION 'Purge failed: % hard-deny rows remain', forbidden_left;
    END IF;
    IF has_qqq = 0 OR has_ixic = 0 THEN
        RAISE EXCEPTION 'Purge failed: missing QQQ or ^IXIC reference row';
    END IF;
END $$;

COMMIT;

VACUUM (ANALYZE) assets;
REINDEX TABLE assets;

-- =====================================================================
-- DONE
-- =====================================================================