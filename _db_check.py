import asyncio, asyncpg, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DSN = "postgresql://postgres:postgres123@localhost:5432/bedaanwaves_db"


async def main():
    try:
        conn = await asyncpg.connect(DSN, timeout=10)
    except Exception as e:
        print(f"DB_CONNECT_ERROR: {e}")
        return

    print("=== symbol_data (master symbol universe) ===")
    row = await conn.fetchrow("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE exchange = 'NASDAQ') AS nasdaq,
            COUNT(*) FILTER (WHERE exchange = 'NASDAQ' AND active_status) AS nasdaq_active,
            COUNT(*) FILTER (WHERE sector IS NULL OR sector = '') AS missing_sector,
            MAX(updated_at) AS last_updated
        FROM symbol_data
    """)
    print(dict(row))

    print("\n=== exchanges in symbol_data ===")
    for r in await conn.fetch(
        "SELECT exchange, COUNT(*) AS total, COUNT(*) FILTER (WHERE active_status) AS active "
        "FROM symbol_data GROUP BY exchange ORDER BY total DESC LIMIT 15"
    ):
        print(dict(r))

    print("\n=== assets table (analytics universe) ===")
    row = await conn.fetchrow("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE market = 'NASDAQ') AS nasdaq,
            COUNT(*) FILTER (WHERE sector IS NULL OR sector = '') AS missing_sector,
            MAX(updated_at) AS last_updated
        FROM assets
    """)
    print(dict(row))

    print("\n=== price data freshness ===")
    row = await conn.fetchrow("""
        SELECT
            (SELECT MAX(timestamp) FROM intl_price_candles) AS latest_candle,
            (SELECT MAX(snapshot_time) FROM market_data_snapshots) AS latest_snapshot,
            (SELECT COUNT(DISTINCT asset_id) FROM market_data_snapshots) AS snapshot_assets
    """)
    print(dict(row))

    await conn.close()


asyncio.run(main())
