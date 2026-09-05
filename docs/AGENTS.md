# BedaanWaves — Agent Reference

## Project layout

```
backend/          FastAPI app (Python 3.11, SQLAlchemy 2.0 async, pytest)
frontend/         Next.js 16 App Router + TypeScript + Tailwind v4 + React Testing Library
docs/             Architecture & design documentation
```

## Common commands

### Backend

```bash
# Run the API server
python -m uvicorn app.main:app --reload --port 3000
# (from the backend/ directory, or: uvicorn app.main:app --reload --port 3000)

# Run tests
python -m pytest

# Lint & type-check Python
ruff check app/          # if ruff is installed
python -m mypy app/      # if mypy is configured
```

### Frontend

```bash
npm run dev               # starts both backend (port 3000) and frontend (port 3005)
cd frontend
npx tsc --noEmit          # TypeScript type-check
npx eslint src/           # Lint source files
npx vitest run            # Run unit + component tests
npx vitest run --typecheck # Run tests with type-checking
npx playwright test       # Run end-to-end tests (if configured)
```

## Test commands (run from repo root)

| Tool          | Command                                                |
|---------------|--------------------------------------------------------|
| Backend tests | `python -m pytest backend/app/tests/`                  |
| Frontend TC   | `cd frontend && npx tsc --noEmit`                      |
| Frontend lint | `cd frontend && npx eslint src/`                       |
| Frontend tests| `cd frontend && npx vitest run`                        |
| E2E tests     | `cd frontend && npx playwright test`                    |

## Important notes

- The password-recovery feature is fully implemented in both `backend/app/` and `frontend/src/`.
- Backend tests live in `backend/app/tests/auth/` and cover both the service layer and the API layer (46 tests, all passing — includes `lang=fa` Persian message coverage for auth and password-recovery endpoints).
- Frontend tests live in `frontend/src/tests/` and cover the FSM hook, page component, API utilities, and UI components.
- The primary brand colour for call-to-action buttons is `#005A9C` (`.btn-primary-brand` class).
