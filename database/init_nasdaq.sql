-- Nasdaq-only launch: additional tables and Nasdaq assets
-- Run: psql -U postgres -d bedaanwaves_db -f database/init_nasdaq.sql

-- ===============================================
-- 1. Generalize fundamentals for all markets
-- ===============================================

-- Add market column to existing Iran-only tables if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='ir_financial_statements' AND column_name='market') THEN
        ALTER TABLE ir_financial_statements ADD COLUMN market VARCHAR(20) DEFAULT 'TSE';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='ir_fundamental_ratios' AND column_name='market') THEN
        ALTER TABLE ir_fundamental_ratios ADD COLUMN market VARCHAR(20) DEFAULT 'TSE';
    END IF;
END $$;

-- Drop old Iran-only unique constraints and add market-aware ones
DROP INDEX IF EXISTS uix_ir_fin_stmt;
DROP INDEX IF EXISTS uix_ir_fund_ratio;

ALTER TABLE ir_financial_statements DROP CONSTRAINT IF EXISTS uix_ir_fin_stmt;
ALTER TABLE ir_fundamental_ratios DROP CONSTRAINT IF EXISTS uix_ir_fund_ratio;

ALTER TABLE ir_financial_statements ADD CONSTRAINT uix_fin_stmt UNIQUE (asset_id, period, statement_type, market);
ALTER TABLE ir_fundamental_ratios ADD CONSTRAINT uix_fund_ratio UNIQUE (asset_id, period, market);

-- ===============================================
-- 2. Board / company leadership table
-- ===============================================
CREATE TABLE IF NOT EXISTS company_leadership (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    leadership_type VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    source VARCHAR(50) DEFAULT 'SEC',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_company_leadership_asset ON company_leadership(asset_id);

-- ===============================================
-- 3. Insert Nasdaq Composite index
-- ===============================================
INSERT INTO assets (symbol, name, asset_class, market, sector, country_code, currency, active, metadata)
VALUES (
    '^IXIC',
    'Nasdaq Composite',
    'INDEX',
    'NASDAQ',
    'Technology',
    'US',
    'USD',
    TRUE,
    '{"description": "Nasdaq Composite Index", "provider": "yfinance"}'::jsonb
)
ON CONFLICT (symbol) DO NOTHING;

-- ===============================================
-- 4. Sample board members for Apple (example)
-- ===============================================
INSERT INTO company_leadership (asset_id, name, title, leadership_type, start_date, source)
SELECT id, 'Timothy D. Cook', 'Chief Executive Officer', 'officer', DATE '2011-08-24', 'SEC'
FROM assets WHERE symbol = 'AAPL'
UNION ALL
SELECT id, 'Luca Maestri', 'Chief Financial Officer', 'officer', DATE '2014-01-01', 'SEC'
FROM assets WHERE symbol = 'AAPL'
UNION ALL
SELECT id, 'Arthur D. Levinson', 'Chairman of the Board', 'board', DATE '2011-08-24', 'SEC'
FROM assets WHERE symbol = 'AAPL'
ON CONFLICT DO NOTHING;

-- ===============================================
-- 5. Sample macro indicators (updated by ingestion service)
-- ===============================================
INSERT INTO macro_indicators (indicator_code, name, value, period, unit, source, as_of)
VALUES
    ('GDP', 'Gross Domestic Product', 27835.0, '2026Q2', 'USD Billions', 'FRED', '2026-07-30'),
    ('UNRATE', 'Unemployment Rate', 4.1, '2026-07', 'Percent', 'FRED', '2026-08-01'),
    ('CPIAUCSL', 'Consumer Price Index', 313.5, '2026-07', 'Index 1982-84=100', 'FRED', '2026-08-01'),
    ('FEDFUNDS', 'Federal Funds Rate', 5.33, '2026-07', 'Percent', 'FRED', '2026-08-01'),
    ('DEXUSEU', 'USD/EUR Exchange Rate', 0.92, '2026-07', 'USD per EUR', 'FRED', '2026-08-01')
ON CONFLICT DO NOTHING;

-- ===============================================
-- 6. Sample English news
-- ===============================================
INSERT INTO news (source, title, body, url, published_at, asset_id, language)
SELECT 'Reuters', 'Fed signals potential rate cut in September', 'Federal Reserve officials indicated they are ready to begin easing monetary policy...', 'https://reuters.com/fed-sept-rate-cut', TIMESTAMP '2026-08-24 09:00:00', id, 'en'
FROM assets WHERE symbol = 'AAPL'
UNION ALL
SELECT 'Bloomberg', 'NVIDIA beats Q2 earnings estimates', 'NVIDIA reported quarterly revenue of $46.7 billion, beating analyst estimates...', 'https://bloomberg.com/nvidia-q2', TIMESTAMP '2026-08-23 16:30:00', id, 'en'
FROM assets WHERE symbol = 'NVDA'
ON CONFLICT DO NOTHING;

-- ===============================================
-- Done
-- ===============================================
SELECT 'Nasdaq tables and sample data created. Run python scripts/seed_nasdaq.py to load all constituents.' AS status;
