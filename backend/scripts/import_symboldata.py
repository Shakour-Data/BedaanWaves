import csv
from io import StringIO
import psycopg2
import requests

NASDAQ_CSV_URL = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed-symbols.csv"

def fetch_and_parse_nasdaq_data():
    response = requests.get(NASDAQ_CSV_URL)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch CSV: {response.status_code}")
    return response.text

def insert_symbols(conn, rows):
    conn.autocommit = True
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    
    try:
        for row in rows:
            symbol = row.get('Symbol', '').strip()
            security_name = row.get('Security Name', '').strip()
            
            if not symbol:
                skipped += 1
                continue
            
            company_name = security_name.split(' - ')[0].strip() if ' - ' in security_name else security_name
            
            market_category = row.get('Market Category', '').strip()
            if market_category == 'G':
                market_type = 'GROWTH'
            elif market_category == 'Q':
                market_type = 'NASDAQ_GLOBAL'
            elif market_category == 'S':
                market_type = 'NASDAQ_CAPITAL'
            else:
                market_type = 'STOCK'
            
            etf_val = row.get('ETF', '').strip()
            etf_flag = etf_val.upper() == 'Y'
            
            test_issue = row.get('Test Issue', '').strip()
            is_test = test_issue.upper() == 'Y'
            
            if etf_val.upper() == 'Y' or test_issue.upper() == 'Y':
                skipped += 1
                continue
            
            try:
                cur.execute('''
                INSERT INTO symbol_data (
                    symbol, security_name, exchange, country_code, index_code,
                    industry_code, market_type, active_status, listing_date,
                    round_lot_size, market_category, financial_status, etf_flag,
                    next_shares, is_test_issue, security_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO NOTHING
                ''', (
                    symbol, security_name, 'NASDAQ', 'US', None,
                    None, market_type, True, None,
                    row.get('Round Lot Size', ''), market_category,
                    row.get('Financial Status', ''), etf_flag,
                    row.get('NextShares', '') == 'Y', is_test, 'COMMON'
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting {symbol}: {e}")
                skipped += 1
            
            if inserted % 500 == 0:
                print(f"Inserted {inserted} symbols...")
        
        conn.commit()
        print(f"Import complete: {inserted} inserted, {skipped} skipped")
        return inserted, skipped
    finally:
        cur.close()

def main():
    print("Fetching NASDAQ listed symbols...")
    csv_text = fetch_and_parse_nasdaq_data()
    
    rows = []
    reader = csv.DictReader(StringIO(csv_text))
    for row in reader:
        if row.get('ETF', '') != 'Y' and row.get('Test Issue', '') != 'Y':
            rows.append(row)
    
    print(f"Fetched {len(rows)} rows (excluding ETFs and test issues)")
    
    print("Connecting to database...")
    conn = psycopg2.connect(
        dbname='bedaanwaves_db',
        user='postgres',
        password='postgres',
        host='localhost',
        port=5432
    )
    
    print("Importing into SymbolData table...")
    insert_symbols(conn, rows)
    
    conn.close()
    print("Done!")

if __name__ == "__main__":
    main()