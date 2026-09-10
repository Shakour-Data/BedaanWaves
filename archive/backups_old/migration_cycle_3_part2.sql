-- Cycle 3 - Part 2: Remaining COMMENTs and roles (macro_forecasts excluded - migration not applied)

\echo '=== Cycle 3 Part 2: Remaining statements ==='

-- COMMENT on macro_forecasts (table doesn't exist - apply its migration first)
-- Will be added when 20260907_add_macro_section migration is run

-- Materialized view comments
COMMENT ON MATERIALIZED VIEW mv_daily_score_trends IS 'Precomputed daily score trends with flattened JSONB dimension scores. Refresh with REFRESH MATERIALIZED VIEW CONCURRENTLY.';

COMMENT ON MATERIALIZED VIEW mv_portfolio_valuation IS 'Precomputed portfolio valuations from latest market data. Refresh with REFRESH MATERIALIZED VIEW CONCURRENTLY.';

-- View comments
COMMENT ON VIEW v_position_valuation IS 'Computed position valuations from latest market_data_snapshots. Use instead of stored computed columns.';

COMMENT ON VIEW latest_prices IS 'Latest price snapshot per asset (real-time).';

COMMENT ON VIEW portfolio_performance IS 'Aggregate portfolio P&L and performance metrics.';

-- ============================================================================
-- 4. Database Roles and GRANT/REVOKE Permissions
-- ============================================================================

\echo '--- Creating database roles and permissions ---'

-- Role: readonly for analytics/reporting tools
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bedaan_readonly') THEN
        CREATE ROLE bedaan_readonly;
    END IF;
END $$;

GRANT CONNECT ON DATABASE bedaanwaves_db TO bedaan_readonly;
GRANT USAGE ON SCHEMA public TO bedaan_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bedaan_readonly;
GRANT SELECT ON mv_daily_score_trends TO bedaan_readonly;
GRANT SELECT ON mv_portfolio_valuation TO bedaan_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO bedaan_readonly;

-- Role: app for FastAPI backend
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bedaan_app') THEN
        CREATE ROLE bedaan_app;
    END IF;
END $$;

GRANT CONNECT ON DATABASE bedaanwaves_db TO bedaan_app;
GRANT USAGE ON SCHEMA public TO bedaan_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bedaan_app;
GRANT SELECT ON mv_daily_score_trends TO bedaan_app;
GRANT SELECT ON mv_portfolio_valuation TO bedaan_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO bedaan_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bedaan_app;

-- Revoke public access for security
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE bedaanwaves_db FROM PUBLIC;

-- ============================================================================
-- 5. Apply the macro_forecasts migration manually
-- ============================================================================

\echo '--- Creating macro_forecasts table ---'

CREATE TABLE IF NOT EXISTS macro_forecasts (
    id              UUID    NOT NULL DEFAULT uuid_generate_v4(),
    indicator_code  VARCHAR(50) NOT NULL,
    model_name      VARCHAR(100) NOT NULL DEFAULT 'ARIMA',
    horizon         INTEGER  NOT NULL,
    frequency       VARCHAR(20) NOT NULL DEFAULT 'monthly',
    forecast_date   DATE     NOT NULL,
    forecast_value  NUMERIC(20,6),
    lower_ci        NUMERIC(20,6),
    upper_ci        NUMERIC(20,6),
    confidence      NUMERIC(5,2) DEFAULT 0.0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_macro_forecast UNIQUE (indicator_code, model_name, horizon, forecast_date)
);

CREATE INDEX IF NOT EXISTS idx_macro_forecasts_code_date
    ON macro_forecasts (indicator_code, forecast_date, horizon);

COMMENT ON TABLE macro_forecasts IS 'In-process macro forecasts (ARIMA/naive) from historical MacroIndicator data. No external API used.';

-- Add the unique constraint that the migration fixes (for macro_indicators)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uix_macro_indicator' 
        AND conrelid = 'macro_indicators'::regclass
    ) THEN
        ALTER TABLE macro_indicators
            ADD CONSTRAINT uix_macro_indicator
            UNIQUE (indicator_code, period);
    END IF;
END $$;

-- Index for latest-per-indicator lookups
CREATE INDEX IF NOT EXISTS idx_macro_indicator_code_as_of
    ON macro_indicators (indicator_code, as_of);

-- ============================================================================
-- Summary
-- ============================================================================

\echo '=== Cycle 3 Part 2: Complete ==='
