# TreasureHunt.Tectrix2026 — Runnable Project

This repository contains a runnable full-stack setup:

- `frontend/`: static web app (HTML/CSS/JS)
- `backend/`: Python API server
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

## Implemented now

- Participant register/login/logout with token sessions
- Group create + invite member + accept/reject invite flow
- One active group per participant and max 4 member checks
- QR scan + one submission per group/QR
- Final QR prerequisite check
- Admin login session + dashboard
- Admin game controls: pause/resume/close, set final QR, broadcast message

## Seeded data

- Admin credentials: `admin@tectrix.edu` / `admin123`
- QR tokens: `token-qr-1`, `token-qr-2`, `token-qr-3`

## Quick test flow

1. Register user A and create group.
2. Register/login user B.
3. Send invite from A to B and accept from B.
4. Scan and submit QR1/QR2 before QR3 final.
5. Login admin and change game state/final QR.

## Docs

- API contract: `api/openapi.yaml`
- Data schema reference: `db/schema.sql`
- Architecture notes: `docs/architecture.md`
