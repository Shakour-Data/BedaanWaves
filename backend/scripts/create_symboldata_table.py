import psycopg2

conn = psycopg2.connect(
    dbname='bedaanwaves_db',
    user='postgres',
    password='postgres',
    host='localhost',
    port=5432
)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute('''
    CREATE TABLE IF NOT EXISTS symbol_data (
        symbol_id SERIAL PRIMARY KEY,
        symbol VARCHAR(10) NOT NULL UNIQUE,
        security_name TEXT NOT NULL,
        exchange VARCHAR(50) NOT NULL DEFAULT 'NASDAQ',
        country_code CHAR(2) NOT NULL DEFAULT 'US',
        index_code VARCHAR(20),
        industry_code VARCHAR(100),
        market_type VARCHAR(20) NOT NULL DEFAULT 'STOCK',
        active_status BOOLEAN DEFAULT TRUE,
        status_reason VARCHAR(200),
        listing_date DATE,
        delisting_date DATE,
        round_lot_size VARCHAR(50),
        market_category CHAR(1),
        financial_status VARCHAR(50),
        etf_flag BOOLEAN DEFAULT FALSE,
        next_shares BOOLEAN DEFAULT FALSE,
        is_test_issue BOOLEAN DEFAULT FALSE,
        security_type VARCHAR(50) DEFAULT 'COMMON',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cur.execute('''
    CREATE INDEX IF NOT EXISTS idx_symbol_data_symbol ON symbol_data(symbol);
    CREATE INDEX IF NOT EXISTS idx_symbol_data_exchange ON symbol_data(exchange);
    CREATE INDEX IF NOT EXISTS idx_symbol_data_country ON symbol_data(country_code);
    CREATE INDEX IF NOT EXISTS idx_symbol_data_market_type ON symbol_data(market_type);
    CREATE INDEX IF NOT EXISTS idx_symbol_data_active ON symbol_data(active_status);
    CREATE INDEX IF NOT EXISTS idx_symbol_data_industry ON symbol_data(industry_code);
    ''')
    
    cur.execute("SELECT symbol FROM symbol_data LIMIT 1")
    count = len(cur.fetchall())
    print(f"SymbolData table created/checked successfully. Current row count: {count}")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()