ALTER TABLE news ADD COLUMN IF NOT EXISTS category VARCHAR(50) NOT NULL DEFAULT 'ECONOMIC';
ALTER TABLE news ADD COLUMN IF NOT EXISTS sub_category VARCHAR(100);
ALTER TABLE news ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE news ADD COLUMN IF NOT EXISTS priority VARCHAR(10) NOT NULL DEFAULT 'NORMAL';
ALTER TABLE news ADD COLUMN IF NOT EXISTS is_market_moving BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE news ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'en';

UPDATE news SET url = COALESCE(url, 'https://bedaanwaves.local/news/' || id::text) WHERE url IS NULL;
ALTER TABLE news ALTER COLUMN url SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_news_category_priority ON news (category, priority);
CREATE INDEX IF NOT EXISTS idx_news_region_category ON news (region, category);
CREATE INDEX IF NOT EXISTS idx_news_url ON news (url);

CREATE TABLE IF NOT EXISTS news_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    region VARCHAR(50),
    interval_seconds INTEGER NOT NULL DEFAULT 900,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    max_concurrent_requests INTEGER NOT NULL DEFAULT 3,
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_error_at TIMESTAMP WITH TIME ZONE,
    last_error_message TEXT,
    success_count_24h INTEGER NOT NULL DEFAULT 0,
    failure_count_24h INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_source_enabled ON news_sources (enabled);
CREATE INDEX IF NOT EXISTS idx_news_source_category ON news_sources (category);
