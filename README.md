# BedaanWaves - Setup Instructions

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ and npm 8+
- Redis (optional, for caching)

## Environment Setup

### Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and set the following required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - A strong random secret key (min 64 chars)
- `JWT_SECRET` - A strong random JWT secret (min 64 chars)

6. Ensure PostgreSQL is running and create the database:
```bash
createdb bedaanwaves_db
```

7. Run database migrations:
```bash
cd backend
alembic upgrade head
```

### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` and set:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1
```

## Running the Application

### Development Mode

From the project root, run:
```bash
npm run dev
```

This starts:
- Backend API server on port 3000
- Frontend Next.js server on port 3005

Access the application at: http://localhost:3005

### Production Mode

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Start the backend:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000
```

3. Start the frontend:
```bash
cd frontend
npm start -p 3005
```

## Default Admin User

On first startup, the application automatically creates an admin user if one doesn't exist.

Check the backend logs for the generated admin password, or set the `ADMIN_PASSWORD` environment variable to use a specific password.

## Port Configuration

| Service | Port | Environment Variable |
|---------|------|---------------------|
| Backend API | 3000 | `API_PORT` |
| Frontend | 3005 | Next.js `-p` flag |

## Troubleshooting

### Backend won't start
- Ensure PostgreSQL is running
- Check that the database exists
- Verify `DATABASE_URL` in `.env` is correct
- Check backend logs for specific errors

### Frontend can't connect to API
- Verify `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
- Ensure backend is running on port 3000
- Check browser console for CORS errors
- Verify `CORS_ORIGINS` in backend `.env` includes `http://localhost:3005`

### Database connection errors
- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Check that the database `bedaanwaves_db` exists

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
