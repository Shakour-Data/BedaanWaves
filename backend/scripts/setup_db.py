"""Database setup script - creates database and runs migrations."""

import os
import sys
import subprocess

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

def create_database():
    """Create bedaanwaves_db database if it doesn't exist."""
    import psycopg2
    
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )
    conn.autocommit = True
    
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("bedaanwaves_db",))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("CREATE DATABASE bedaanwaves_db")
        print("✅ Database bedaanwaves_db created")
    else:
        print("✅ Database bedaanwaves_db already exists")
    
    cursor.close()
    conn.close()

def run_migrations():
    """Run alembic migrations."""
    # Update alembic.ini with correct URL
    alembic_ini_path = "database/alembic.ini"
    
    with open(alembic_ini_path, "r") as f:
        content = f.read()
    
    # Update sqlalchemy.url
    content = content.replace(
        'sqlalchemy.url = driver://user:pass@localhost/dbname',
        'sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/bedaanwaves_db'
    )
    
    with open(alembic_ini_path, "w") as f:
        f.write(content)
    
    # Run alembic
    result = subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"],
        cwd="database",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Migrations applied successfully")
    else:
        print(f"⚠️ Migration output: {result.stdout}")
        print(f"⚠️ Migration errors: {result.stderr}")

def main():
    """Main setup routine."""
    try:
        create_database()
    except Exception as e:
        print(f"Database creation error: {e}")
        return
    
    try:
        run_migrations()
    except Exception as e:
        print(f"Migration error: {e}")
        return

if __name__ == "__main__":
    main()