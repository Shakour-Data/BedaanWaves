-- Comprehensive Database Population Script
-- Run this with: psql -h localhost -U postgres -d bedaanwaves_db -f populate_database.sql

\set ON_ERROR_STOP on

-- Clear existing data
DELETE FROM ml_signals;
DELETE FROM financial_statements;
DELETE FROM news_articles;
DELETE FROM market_data_snapshots;
DELETE FROM raw_market_data;
DELETE FROM crypto_price_candles;
DELETE FROM intl_price_candles;
DELETE FROM price_candles;
DELETE FROM positions;
DELETE FROM portfolios;
DELETE FROM alerts;
DELETE FROM users;

-- Insert core assets (Crypto, NASDAQ symbols)
INSERT INTO assets (id, symbol, name, asset_class, market, country_code, currency, sector, sub_sector, active, created_at, updated_at, metadata) VALUES
-- Crypto
(1, 'BTCUSD', 'Bitcoin', 'CRYPTO', 'BINANCE', 'GLOBAL', 'USD', NULL, NULL, true, NOW(), NOW(), '{}'),
(2, 'ETHUSD', 'Ethereum', 'CRYPTO', 'BINANCE', 'GLOBAL', 'USD', NULL, NULL, true, NOW(), NOW(), '{}'),
(3, 'ADAUSD', 'Cardano', 'CRYPTO', 'BINANCE', 'GLOBAL', 'USD', NULL, NULL, true, NOW(), NOW(), '{}'),
(4, 'XRPUSD', 'XRP', 'CRYPTO', 'BINANCE', 'GLOBAL', 'USD', NULL, NULL, true, NOW(), NOW(), '{}'),
(5, 'DOGEUSD', 'Dogecoin', 'CRYPTO', 'BINANCE', 'GLOBAL', 'USD', NULL, NULL, true, NOW(), NOW(), '{}'),
-- NASDAQ
(6, 'AAPL', 'Apple Inc.', 'EQUITY', 'NASDAQ', 'US', 'USD', 'Technology', 'Consumer Electronics', true, NOW(), NOW(), '{}'),
(7, 'GOOGL', 'Google LLC', 'EQUITY', 'NASDAQ', 'US', 'USD', 'Technology', 'Internet Services', true, NOW(), NOW(), '{}'),
(8, 'MSFT', 'Microsoft Corp', 'EQUITY', 'NASDAQ', 'US', 'USD', 'Technology', 'Software', true, NOW(), NOW(), '{}'),
(9, 'TSLA', 'Tesla Inc.', 'EQUITY', 'NASDAQ', 'US', 'USD', 'Automotive', 'Electric Vehicles', true, NOW(), NOW(), '{}'),
(10, 'AMZN', 'Amazon.com Inc.', 'EQUITY', 'NASDAQ', 'US', 'USD', 'Technology', 'E-commerce', true, NOW(), NOW(), '{}');

-- Generate 3 years of price candles (daily OHLCV)
-- Note: This is a simplified approach - in production, you'd use a data generation script
DO $$
DECLARE
    start_date DATE := '2023-08-06';
    end_date DATE := CURRENT_DATE;
    current_date DATE := start_date;
    asset_id INT;
    base_price NUMERIC;
    open_price NUMERIC;
    close_price NUMERIC;
    high_price NUMERIC;
    low_price NUMERIC;
    volume BIGINT;
    turnover NUMERIC;
    transactions INT;
    market TEXT;
BEGIN
    FOR asset_id IN SELECT id FROM assets LOOP
        base_price := 100 + (asset_id * 100);
        current_date := start_date;
        
        WHILE current_date <= end_date LOOP
            -- Generate realistic price movement
            open_price := base_price + (RANDOM() - 0.5) * 50;
            close_price := open_price + (RANDOM() - 0.5) * 20;
            high_price := GREATEST(open_price, close_price) + RANDOM() * 10;
            low_price := LEAST(open_price, close_price) - RANDOM() * 10;
            volume := 100000 + FLOOR(RANDOM() * 10000000);
            turnover := volume * close_price;
            transactions := FLOOR(RANDOM() * 10000);
            
            INSERT INTO price_candles (asset_id, timeframe, timestamp, open, high, low, close, volume, turnover, transactions)
            VALUES (asset_id, '1d', current_date, open_price, high_price, low_price, close_price, volume, turnover, transactions);
            
            -- Also insert into market-specific tables
            SELECT market INTO market FROM assets WHERE id = asset_id;
            IF market IN ('NASDAQ', 'NYSE') THEN
                INSERT INTO intl_price_candles (asset_id, timeframe, timestamp, open, high, low, close, volume, turnover, transactions)
                VALUES (asset_id, '1d', current_date, open_price, high_price, low_price, close_price, volume, turnover, transactions);
            ELSIF market IN ('BINANCE', 'KRAKEN', 'COINBASE') THEN
                INSERT INTO crypto_price_candles (asset_id, timeframe, timestamp, open, high, low, close, volume, turnover, transactions)
                VALUES (asset_id, '1d', current_date, open_price, high_price, low_price, close_price, volume, turnover, transactions);
            END IF;
            
            current_date := current_date + INTERVAL '1 day';
            base_price := close_price;
        END LOOP;
    END LOOP;
END $$;

-- Insert sample users
INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at) VALUES
(1, 'admin@example.com', 'admin_hash_password', 'System Administrator', true, true, NOW(), NOW()),
(2, 'test@example.com', 'test_hash_password', 'Test User', true, false, NOW(), NOW());

-- Insert sample portfolios
INSERT INTO portfolios (id, user_id, name, description, cash_balance, currency, created_at, updated_at) VALUES
(1, 1, 'Long Term Growth', 'Test portfolio for analysis', 50000.00, 'USD', NOW(), NOW()),
(2, 2, 'Daily Trader', 'Test portfolio for trading', 25000.00, 'USD', NOW(), NOW());

-- Insert sample positions
INSERT INTO positions (id, portfolio_id, asset_id, quantity, avg_cost, created_at, updated_at) VALUES
(1, 1, 6, 500.0000, 150.50, NOW(), NOW()),  -- AAPL
(2, 1, 1, 2.5000, 45000.00, NOW(), NOW()),   -- BTC
(3, 2, 6, 100.0000, 160.00, NOW(), NOW());    -- AAPL

-- Insert sample crypto price candles for hourly-level analysis
DO $$
DECLARE
    start_time TIMESTAMP := '2026-08-06 00:00:00';
    current_time TIMESTAMP := start_time;
    end_time TIMESTAMP := CURRENT_TIMESTAMP;
    asset_id INT := 1;  -- BTC
BEGIN
    WHILE current_time <= end_time LOOP
        INSERT INTO crypto_price_candles (asset_id, timeframe, timestamp, open, high, low, close, volume, turnover, transactions)
        VALUES (
            asset_id,
            '1h',
            current_time,
            55000 + (RANDOM() - 0.5) * 1000,
            55500 + (RANDOM() - 0.5) * 1500,
            54500 + (RANDOM() - 0.5) * 1000,
            55200 + (RANDOM() - 0.5) * 800,
            1000 + FLOOR(RANDOM() * 50000),
            0,
            FLOOR(RANDOM() * 500)
        );
        current_time := current_time + INTERVAL '1 hour';
    END LOOP;
END $$;

-- Insert sample raw market data (every 15 minutes)
DO $$
DECLARE
    start_time TIMESTAMP := '2023-08-06 09:00:00';
    current_time TIMESTAMP := start_time;
    end_time TIMESTAMP := CURRENT_TIMESTAMP;
    i INT := 1;
BEGIN
    WHILE current_time <= end_time LOOP
        INSERT INTO raw_market_data (asset_id, timestamp, source, data, raw_json, processed)
        VALUES (
            (i % 10) + 1,
            current_time,
            'simulation',
            jsonb_build_object(
                'price', round(100 + (i % 5000), 2),
                'bid', round(100 + (i % 5000) - 0.5, 2),
                'ask', round(100 + (i % 5000) + 0.5, 2),
                'volume', (100 + i * 100)::bigint,
                'spread', round(random() * 0.1, 2)
            ),
            '{}',
            false
        );
        current_time := current_time + INTERVAL '15 minutes';
        i := i + 1;
    END LOOP;
END $$;

-- Insert sample market snapshots
DO $$
DECLARE
    current_date DATE := '2023-08-06';
    end_date DATE := CURRENT_DATE;
    asset_id INT;
    open_price NUMERIC;
    high_price NUMERIC;
    low_price NUMERIC;
    close_price NUMERIC;
    volume BIGINT;
BEGIN
    WHILE current_date <= end_date LOOP
        FOR asset_id IN SELECT id FROM assets LOOP
            open_price := 100 + (asset_id * 100) + (RANDOM() - 0.5) * 20;
            close_price := open_price + (RANDOM() - 0.5) * 10;
            high_price := GREATEST(open_price, close_price) + RANDOM() * 5;
            low_price := LEAST(open_price, close_price) - RANDOM() * 5;
            volume := 1000000 + FLOOR(RANDOM() * 100000000);
            
            INSERT INTO market_data_snapshots (
                asset_id, timeframe, timestamp, open_price, high_price, low_price, 
                close_price, volume, adjusted_close, indicators, created_at
            ) VALUES (
                asset_id, '1d', current_date, open_price, high_price, low_price,
                close_price, volume, close_price * 1.001,
                jsonb_build_object(
                    'rsi', round(random() * 60 + 20, 2),
                    'macd', round((random() - 0.5) * 2, 4),
                    'sma_20', round(close_price * (0.98 + random() * 0.04), 2),
                    'sma_50', round(close_price * (0.95 + random() * 0.1), 2)
                )::jsonb,
                current_date
            );
        END LOOP;
        current_date := current_date + INTERVAL '1 day';
    END LOOP;
END $$;

-- Insert sample financial statements
DO $$
DECLARE
    base_revenue NUMERIC := 10000000;
    asset_id INT;
    year INT;
    revenue NUMERIC;
    market VARCHAR(20);
BEGIN
    FOR asset_id IN SELECT id FROM assets LOOP
        SELECT market INTO market FROM assets WHERE id = asset_id;
        FOR year IN 2023..2025 LOOP
            revenue := base_revenue * (0.9 + RANDOM() * 0.6);
            
            -- Balance Sheet
            INSERT INTO financial_statements (
                asset_id, market, statement_type, period, fiscal_year, as_of, data
            ) VALUES (
                asset_id, market, 'balance_sheet', year || '-annual', year,
                date(year, 12, 31),
                jsonb_build_object(
                    'revenue', revenue,
                    'net_income', revenue * 0.1,
                    'total_assets', revenue * 5,
                    'total_liabilities', revenue * 2,
                    'shareholders_equity', revenue * 3,
                    'cash', revenue * 0.3,
                    'debt', revenue * 1.5
                )
            );
            
            -- Income Statement
            INSERT INTO financial_statements (
                asset_id, market, statement_type, period, fiscal_year, as_of, data
            ) VALUES (
                asset_id, market, 'income_statement', year || '-annual', year,
                date(year, 12, 31),
                jsonb_build_object(
                    'revenue', revenue,
                    'gross_profit', revenue * 0.5,
                    'operating_expense', revenue * 0.3,
                    'operating_income', revenue * 0.2,
                    'net_income', revenue * 0.1,
                    'eps_basic', (revenue * 0.1 / 1000)::numeric(10, 2),
                    'eps_diluted', (revenue * 0.1 / 1050)::numeric(10, 2)
                )
            );
            
            -- Cash Flow
            INSERT INTO financial_statements (
                asset_id, market, statement_type, period, fiscal_year, as_of, data
            ) VALUES (
                asset_id, market, 'cash_flow_statement', year || '-annual', year,
                date(year, 12, 31),
                jsonb_build_object(
                    'operating_cash_flow', revenue * 0.08,
                    'investing_cash_flow', revenue * -0.2,
                    'financing_cash_flow', revenue * 0.15,
                    'free_cash_flow', revenue * 0.05
                )
            );
        END LOOP;
    END LOOP;
END $$;

-- Insert sample news articles
DO $$
DECLARE
    current_date DATE := '2025-01-01';
    end_date DATE := CURRENT_DATE;
    headlines TEXT[];
    sentiment TEXT;
    i INT;
BEGIN
    headlines := ARRAY[
        'Earnings beat expectations',
        'Product launch announced',
        'Partnership formed',
        'Market expansion confirmed',
        'Regulatory approval granted',
        'Earnings miss forecasts',
        'Product recall announced',
        'Investigation opened',
        'Market share declining',
        'Leadership transition'
    ];
    
    WHILE current_date <= end_date LOOP
        -- Generate 1-2 news items per day
        FOR i IN 1..(1 + FLOOR(RANDOM() * 2))::INT LOOP
            sentiment := CASE 
                WHEN RANDOM() < 0.3 THEN 'positive'
                WHEN RANDOM() < 0.6 THEN 'negative'
                ELSE 'neutral'
            END;
            
            INSERT INTO news_articles (
                asset_id, headline, summary, content, url, source,
                published_at, sentiment_score, language, created_at
            ) VALUES (
                (1 + FLOOR(RANDOM() * 10))::INT,
                headlines[(1 + FLOOR(RANDOM() * 10))::INT],
                'Market news for ' || current_date::TEXT,
                'Detailed article content would go here...',
                'https://news.example.com/' || current_date::TEXT || '/article' || (i + 1),
                'synthetic-news-source',
                current_date + (RANDOM() * 8 + 8)::INT / 24::REAL * INTERVAL '1 hour',
                CASE sentiment
                    WHEN 'positive' THEN 0.8
                    WHEN 'negative' THEN 0.2
                    ELSE 0.5
                END,
                'en',
                current_date
            );
        END LOOP;
        current_date := current_date + INTERVAL '1 day';
    END LOOP;
END $$;

-- Insert sample ML signals
DO $$
DECLARE
    current_date DATE := CURRENT_DATE - INTERVAL '30 days';
    end_date DATE := CURRENT_DATE;
    asset_id INT;
BEGIN
    WHILE current_date <= end_date LOOP
        FOR asset_id IN SELECT id FROM assets LOOP
            INSERT INTO ml_signals (
                asset_id, timestamp, model_name, signal_type, confidence,
                predicted_price, actual_price, direction, features_used, raw_output
            ) VALUES (
                asset_id,
                current_date + (RANDOM() * 10 + 8) / 24::REAL * INTERVAL '1 hour',
                'LSTM-Predictor-v1',
                'prediction',
                round(0.5 + RANDOM() * 0.4, 4),
                100 + (asset_id * 100) + (RANDOM() - 0.5) * 20,
                100 + (asset_id * 100) + (RANDOM() - 0.5) * 20,
                CASE WHEN RANDOM() < 0.5 THEN 'up' ELSE 'down' END,
                jsonb_build_object(
                    'rsi', round(20 + RANDOM() * 60, 2),
                    'macd', round((RANDOM() - 0.5) * 2, 4),
                    'volume_ma', round(1000000 + RANDOM() * 10000000, 2)
                ),
                '{"predictions": [' || (SELECT string_agg(round(100 + (asset_id * 100) + (RANDOM() - 0.5) * 10, 2)::TEXT, ',')) || '], "uncertainty": 0.1}'
            );
        END LOOP;
        current_date := current_date + INTERVAL '1 day';
    END LOOP;
END $$;

-- Insert sample alerts
INSERT INTO alerts (id, asset_id, user_id, alert_type, condition_value, triggered, created_at)
SELECT 
    generate_series(1, 50),
    (generate_series(1, 50) % 10) + 1,
    (generate_series(1, 50) % 2) + 1,
    CASE (generate_series(1, 50) % 4)
        WHEN 0 THEN 'price_above'
        WHEN 1 THEN 'price_below'
        WHEN 2 THEN 'volume_spike'
        WHEN 3 THEN 'news_sentiment'
    END,
    round(100 + (generate_series(1, 50) % 5000)::numeric, 2),
    RANDOM() < 0.3,
    CURRENT_DATE - (generate_series(1, 50) % 365 || ' days')::INTERVAL
FROM generate_series(1, 50);

-- Update statistics
ANALYZE;

-- Print summary
SELECT table_name, n_tup_ins AS rows_inserted 
FROM pg_stat_user_tables 
WHERE schemaname = 'public' 
ORDER BY table_name;
