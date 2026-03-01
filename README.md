# TreasureHunt.Tectrix2026 — Runnable Project

This repository now contains an actual runnable full-stack setup:

- `frontend/`: static web app (HTML/CSS/JS)
- `backend/`: Python API server (no external dependencies)
- `backend/migrations/`: SQL migration files applied to SQLite

## Run locally

```bash
make migrate
make backend
# open another terminal
make frontend
```

- Frontend: http://localhost:5173
- Backend: http://localhost:4000
- Health endpoint: `GET /health`

## Implemented flows

- Participant registration with unique email + roll
- Group creation with one-active-group-per-participant rule
- QR scan by token
- Mandatory answer/explanation submissions
- One submit per team per QR
- Final QR requires prior submission of non-final QR set
- Admin login and dashboard stats

## Seeded data

Migration seeds:
- Admin credentials: `admin@tectrix.edu` / `admin123`
- QR tokens: `token-qr-1`, `token-qr-2`, `token-qr-3`

## Project docs

- API contract: `api/openapi.yaml`
- Data schema reference: `db/schema.sql`
- Architecture notes: `docs/architecture.md`
