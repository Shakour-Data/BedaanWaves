import psycopg2

conn = psycopg2.connect(
    dbname='bedaanwaves_db',
    user='postgres',
    password='postgres',
    host='localhost',
    port=5432
)
cur = conn.cursor()

print("=== SYMBOL DATA VALIDATION REPORT ===")

# Total count
cur.execute("SELECT COUNT(*) FROM symbol_data")
total = cur.fetchone()[0]
print(f"Total symbols in SymbolData: {total}")

# Exchange breakdown
cur.execute("""
SELECT exchange, COUNT(*) as count 
FROM symbol_data 
GROUP BY exchange 
ORDER BY count DESC
""")
print("\nExchange breakdown:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} symbols")

# Market type breakdown
cur.execute("""
SELECT market_type, COUNT(*) as count 
FROM symbol_data 
GROUP BY market_type 
ORDER BY count DESC
""")
print("\nMarket type breakdown:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} symbols")

# Country breakdown
cur.execute("""
SELECT country_code, COUNT(*) as count 
FROM symbol_data 
GROUP BY country_code 
ORDER BY count DESC
""")
print("\nCountry breakdown:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} symbols")

# Active vs inactive
cur.execute("""
SELECT active_status, COUNT(*) as count 
FROM symbol_data 
GROUP BY active_status
""")
print("\nActive status breakdown:")
for row in cur.fetchall():
    print(f"  Active: {row[0]}: {row[1]} symbols")

# Sample of data
cur.execute("""
SELECT symbol, security_name, exchange, country_code, market_type 
FROM symbol_data 
ORDER BY symbol 
LIMIT 10
""")
print("\nSample symbols:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]}, {row[3]}, {row[4]})")

# Check for any potential data quality issues
cur.execute("""
SELECT symbol 
FROM symbol_data 
WHERE symbol IS NULL OR symbol = '' OR LENGTH(symbol) > 10
""")
bad_symbols = cur.fetchall()
if bad_symbols:
    print(f"\nWARNING: Found {len(bad_symbols)} problematic symbols:")
    for row in bad_symbols[:5]:
        print(f"  {row[0]}")
else:
    print("\n�� All symbols are valid")

cur.execute("""
SELECT symbol 
FROM symbol_data 
WHERE security_name IS NULL OR security_name = ''
""")
bad_names = cur.fetchall()
if bad_names:
    print(f"WARNING: Found {len(bad_names)} symbols with missing names")
else:
    print("�� All symbols have valid security names")

cur.close()
conn.close()

print("\n=== VALIDATION COMPLETE ===")
