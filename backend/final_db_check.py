#!/usr/bin/env python
import sys
sys.path.insert(0, '.')
import asyncio
from app.db.base import get_async_session
from sqlalchemy import text

async def check_data():
    output_lines = []
    async for session in get_async_session():
        tables = ['price_candles', 'ir_price_candles', 'intl_price_candles', 
                  'crypto_price_candles', 'raw_market_data', 'market_data_snapshots',
                  'ml_signals', 'financial_statements', 'news_articles']
        output_lines.append('Database Tables Check:')
        for table_name in tables:
            try:
                cnt = await session.execute(text(f'SELECT COUNT(*) FROM {table_name}'))
                count = cnt.scalar()
                status = '[OK]' if count > 0 else '[EMPTY]'
                output_lines.append(f'  {status} {table_name}: {count:,} rows')
            except Exception as e:
                output_lines.append(f'  [ERROR] {table_name}: {e}')
        
        # Check latest price_candles timestamp
        try:
            result = await session.execute(text('SELECT MAX(timestamp) FROM price_candles'))
            max_ts = result.scalar()
            output_lines.append(f'  [OK] Latest price_candles timestamp: {max_ts}')
        except Exception as e:
            output_lines.append(f'  [ERROR] Price candles timestamp check: {e}')
        
        # Check assets
        try:
            result = await session.execute(text('SELECT COUNT(*) FROM assets'))
            count = result.scalar()
            output_lines.append(f'  [OK] Total assets: {count}')
        except Exception as e:
            output_lines.append(f'  [ERROR] Asset check: {e}')
        break
    
    # Write results to file
    with open('db_check_results.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print("Results saved to db_check_results.txt")

asyncio.run(check_data())