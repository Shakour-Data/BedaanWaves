#!/usr/bin/env python
import sqlalchemy
from sqlalchemy import create_engine
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

conn = engine.connect()
result = conn.exec_driver_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = [row[0] for row in result.fetchall()]
print('Existing tables:', tables)
conn.close()