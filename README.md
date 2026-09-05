# BedaanWaves - Setup Instructions (Native Execution - No Docker Required)

## Overview

BedaanWaves is designed to run natively on your operating system without any Docker or containerization dependencies. All components run directly on the host system using standard development tools and services.

## Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **PostgreSQL 14+** - Primary database
- **Node.js 18+** and **npm 8+** - Frontend runtime
- **Git** - Version control

### Optional Software

- **Redis** (or Memurai on Windows) - For caching layer (optional, application works without it)
- **uv** - Fast Python package installer (alternative to pip)

## Platform-Specific Setup

### Windows

1. **Install Python 3.11+**
   - Download from https://www.python.org/downloads/windows/
   - Ensure "Add Python to PATH" is checked during installation

2. **Install PostgreSQL 14+**
   - Download from https://www.postgresql.org/download/windows/
   - Remember the superuser password (default: `postgres`)
   - Default port: `5432`

3. **Install Node.js 18+**
   - Download from https://nodejs.org/en/download/
   - npm is included with Node.js

4. **Install Redis (Optional)**
   - Download Redis for Windows from https://github.com/microsoftarchive/redis/releases
   - Or use Memurai: https://www.memurai.com/
   - Default port: `6379`

### macOS

1. **Install Dependencies via Homebrew**
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install all prerequisites
   brew install python@3.11 postgresql@14 node@18 redis
   ```

2. **Start PostgreSQL**
   ```bash
   brew services start postgresql@14
   ```

3. **Start Redis (Optional)**
   ```bash
   brew services start redis
   ```

### Linux (Ubuntu/Debian)

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip postgresql-14 postgresql-contrib nodejs npm redis-server
   ```

2. **Start PostgreSQL**
   ```bash
   sudo systemctl enable --now postgresql
   ```

3. **Start Redis (Optional)**
   ```bash
   sudo systemctl enable --now redis-server
   ```

## Environment Setup

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   
   # macOS/Linux
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # Windows (Command Prompt)
   venv\Scripts\activate.bat
   
   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your preferred text editor
   ```
   
   Required variables to configure:
   - `DATABASE_URL` - PostgreSQL connection string (e.g., `postgresql://postgres:yourpassword@localhost:5432/bedaanwaves_db`)
   - `SECRET_KEY` - A strong random secret key (min 64 characters)
   - `JWT_SECRET` - A strong random JWT secret (min 64 characters)
   
   Optional variables:
   - `REDIS_URL` - Redis connection URL (default: `redis://localhost:6379/0`)
   - `CACHE_ENABLED` - Set to `True` if Redis is installed (default: `False`)
   - `API_PORT` - Backend port (default: `3000`)

6. **Create PostgreSQL database:**
   ```bash
   # Using psql
   psql -U postgres -c "CREATE DATABASE bedaanwaves_db;"
   
   # Or using createdb command
   createdb -U postgres bedaanwaves_db
   ```

7. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

8. **Initialize database with sample data (optional):**
   ```bash
   # Run the seed script to populate initial data
   python scripts/seed_real_data.py
   ```

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   ```bash
   # Copy the example environment file (if it exists)
   cp .env.example .env.local 2>/dev/null || echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1" > .env.local
   ```
   
   Edit `.env.local` and set:
   ```
   NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1
   ```

## Running the Application

### Development Mode

From the project root directory:

```bash
# Start both backend and frontend concurrently
npm run dev
```

This command starts:
- **Backend API server** on port `3000` (configurable via `API_PORT` in `.env`)
- **Frontend Next.js server** on port `3005`

Access the application at: http://localhost:3005

#### Running Services Individually

**Backend only:**
```bash
cd backend
.\venv\Scripts\activate  # Windows
# or source venv/bin/activate  # macOS/Linux
uvicorn app.main:app --reload --port 3000 --host 0.0.0.0
```

**Frontend only:**
```bash
cd frontend
npm run dev
```

### Production Mode

1. **Build the frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Start the backend:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --workers 4
   ```

3. **Start the frontend:**
   ```bash
   cd frontend
   npm start -p 3005
   ```

## Native Service Management

### Windows (PowerShell)

Create a service script `start-services.ps1`:
```powershell
# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\path\to\backend'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 3000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\path\to\frontend'; npm run dev"
```

### macOS/Linux (systemd)

Create `/etc/systemd/system/bedaanwaves-backend.service`:
```ini
[Unit]
Description=BedaanWaves Backend
After=network.target postgresql.service

[Service]
Type=simple
User=yourusername
WorkingDirectory=/opt/bedaanwaves/backend
Environment="PATH=/opt/bedaanwaves/backend/venv/bin"
ExecStart=/opt/bedaanwaves/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/bedaanwaves-frontend.service`:
```ini
[Unit]
Description=BedaanWaves Frontend
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/opt/bedaanwaves/frontend
ExecStart=/usr/bin/npm start -- -p 3005
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bedaanwaves-backend.service
sudo systemctl enable --now bedaanwaves-frontend.service
```

## Database Management

### Running Migrations

```bash
cd backend
alembic upgrade head
```

### Creating Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Database Backup

```bash
# Backup
pg_dump -U postgres bedaanwaves_db > backup.sql

# Restore
psql -U postgres bedaanwaves_db < backup.sql
```

## Configuration Reference

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres123@localhost:5432/bedaanwaves_db` | PostgreSQL connection string |
| `SECRET_KEY` | (required) | Application secret key (min 64 chars) |
| `JWT_SECRET` | (required) | JWT signing secret (min 64 chars) |
| `API_PORT` | `3000` | Backend server port |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CACHE_ENABLED` | `False` | Enable/disable caching |
| `CACHE_BACKEND` | `memory` | Cache backend (`memory` or `redis`) |
| `REQUIRE_AUTH` | `True` | Enable authentication |
| `DEBUG` | `False` | Enable debug mode |
| `ENVIRONMENT` | `development` | Environment (`development`, `staging`, `production`) |

### Frontend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:3000/api/v1` | Backend API URL |

## Default Admin User

On first startup, the application automatically creates an admin user if one doesn't exist.

- Check the backend logs for the generated admin password
- Or set the `ADMIN_PASSWORD` environment variable in `.env` to use a specific password
- Default admin username: `admin`

## Port Configuration

| Service | Default Port | Environment Variable / Flag |
|---------|-------------|----------------------------|
| Backend API | 3000 | `API_PORT` in `.env` |
| Frontend | 3005 | Next.js `-p` flag |
| PostgreSQL | 5432 | PostgreSQL config |
| Redis | 6379 | Redis config |

## Troubleshooting

### Backend won't start

- Ensure PostgreSQL is running: `pg_isready -U postgres` or check Windows Services
- Verify database exists: `psql -U postgres -l`
- Check `DATABASE_URL` in `.env` matches your PostgreSQL credentials
- Ensure virtual environment is activated
- Check backend logs for specific error messages

### Frontend can't connect to API

- Verify `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
- Ensure backend is running on port 3000
- Check browser console for CORS errors
- Verify `CORS_ORIGINS` in backend `.env` includes `http://localhost:3005`
- Check firewall settings if connecting from another device

### Database connection errors

- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Check that the database `bedaanwaves_db` exists
- Verify PostgreSQL is accepting connections on the correct port

### Redis connection errors (if enabled)

- Ensure Redis server is running: `redis-cli ping` should return `PONG`
- Check `REDIS_URL` in `.env` matches your Redis installation
- Verify firewall allows connections to port 6379
- The application will fall back to in-memory caching if Redis is unavailable

## Testing

### Backend tests
```bash
cd backend
python -m pytest
```

### Frontend type check
```bash
cd frontend
npx tsc --noEmit
```

### Frontend tests
```bash
cd frontend
npm run test
```

## Project Structure

```
BedaanWaves/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── db/             # Database models and sessions
│   │   ├── infrastructure/ # Infrastructure implementations
│   │   ├── services/       # Business logic services
│   │   └── main.py         # Application entry point
│   ├── alembic.ini         # Alembic configuration
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Backend environment variables
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities and helpers
│   ├── package.json       # Node.js dependencies
│   └── .env.local         # Frontend environment variables
├── database/               # SQL scripts
│   ├── init_nasdaq.sql
│   └── insert_nasdaq_symbols.sql
├── deployment/             # Deployment configurations
│   ├── redis/              # Redis configuration files
│   └── setup.sh            # Setup script (Linux/macOS)
└── docs/                   # Documentation
```

## Important Notes

1. **No Docker Required**: This project is designed to run natively on Windows, macOS, or Linux without any Docker or containerization.

2. **Redis is Optional**: The application works without Redis. When Redis is not available, it automatically falls back to in-memory caching.

3. **Auto-initialization**: The backend automatically:
   - Creates required directories
   - Runs database migrations on startup
   - Seeds initial data if database is empty
   - Creates default admin user

4. **Security**: In production:
   - Always set strong `SECRET_KEY` and `JWT_SECRET` values
   - Keep `REQUIRE_AUTH=True`
   - Keep `DEBUG=False`
   - Use HTTPS (`ENABLE_HTTPS=True`)
   - Configure proper `CORS_ORIGINS`

## Documentation

| Document | Path |
|----------|------|
| End-User Guide | [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) |
| API Reference (all endpoints) | [`docs/05_api/API_REFERENCE.md`](docs/05_api/API_REFERENCE.md) |
| Swagger UI (interactive) | `http://localhost:3000/api/v1/docs` |
| ReDoc | `http://localhost:3000/api/v1/redoc` |
| Architecture Overview | [`docs/AUDIT_REPORT.md`](docs/AUDIT_REPORT.md) |

## Support

For issues and questions:
- Check the `docs/` directory for detailed documentation
- Review application logs in `backend/logs/`
- Check browser console for frontend errors
