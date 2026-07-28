import psycopg2

try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='postgres',
        host='localhost',
        port=5432
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'bedaanwaves_db'")
    exists = cur.fetchone()
    
    if not exists:
        cur.execute('CREATE DATABASE bedaanwaves_db')
        print('Database created successfully')
    else:
        print('Database already exists')
    
    cur.close()
    conn.close()
except Exception as e:
    print(f'Error: {e}')