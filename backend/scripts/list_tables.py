import psycopg2

conn = psycopg2.connect('dbname=bedaanwaves_db user=postgres password=postgres host=localhost port=5432')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = [row[0] for row in cur.fetchall()]
print('Tables:', tables)
cur.close()
conn.close()