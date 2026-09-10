-- ============================================================================
-- Recreate latest_prices and portfolio_performance views
-- Updated to source from intl_price_candles instead of dropped ir_price_candles
-- ============================================================================

\echo '--- Recreating latest_prices view ---'

CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (asset_id)
    asset_id,
    "timestamp",
    close AS current_price,
    (close - open) AS day_change,
    ROUND(((close - open) / open) * 100, 2) AS day_change_pct
FROM intl_price_candles
WHERE timeframe = '1d'
ORDER BY asset_id, "timestamp" DESC;

COMMENT ON VIEW latest_prices IS
    'Latest daily price snapshot per asset. Sources from intl_price_candles (1d timeframe).';

\echo '--- Recreating portfolio_performance view ---'

CREATE OR REPLACE VIEW portfolio_performance AS
SELECT
    p.id AS portfolio_id,
    p.user_id,
    COALESCE(SUM(pos.quantity * lp.current_price), 0) AS total_value,
    COALESCE(SUM(pos.quantity * pos.entry_price), 0) AS total_cost,
    COALESCE(SUM(pos.quantity * lp.current_price), 0) - COALESCE(SUM(pos.quantity * pos.entry_price), 0) AS total_return
FROM portfolios p
LEFT JOIN positions pos ON p.id = pos.portfolio_id
LEFT JOIN latest_prices lp ON pos.asset_id = lp.asset_id
GROUP BY p.id, p.user_id;

COMMENT ON VIEW portfolio_performance IS
    'Aggregate portfolio P&L and performance metrics. Joins portfolios, positions, and latest_prices.';

\echo '--- Views recreated successfully ---'

-- Verify
SELECT count(*) AS view_count FROM pg_views WHERE viewname IN ('latest_prices', 'portfolio_performance');
