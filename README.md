# TreasureHunt.Tectrix2026 — Runnable Project

This repository now contains a runnable MVP with improved security, admin controls, realtime updates, camera QR scanning, aligned API contract, and automated integration tests.

## Run locally

```bash
make migrate
make backend
# open another terminal
make frontend
```

- Frontend: http://localhost:5173
- Backend: http://localhost:4000
- Health: `GET /health`

## Implemented scope

- Secure participant/admin auth with PBKDF2-hashed passwords
- Session tokens with expiry (`expires_at`)
- Group creation + invite + accept/reject, with one-group and max-4 checks
- QR scan + answer submission with final-QR prerequisite enforcement
- Admin dashboard + game state + set final QR + broadcast
- Admin disqualify-team endpoint
- Admin QR editing endpoint (question + active status)
- Realtime admin stream over SSE (`/events`)
- Frontend camera-based QR scanner (BarcodeDetector) with manual-token fallback
- Automated API integration tests (`python3 -m unittest tests/test_api.py`)

## Seeded defaults

- Admin login: `admin@tectrix.edu` / `admin123`
- QR tokens: `token-qr-1`, `token-qr-2`, `token-qr-3`

## Quick test

```bash
python3 -m unittest tests/test_api.py
```

## Docs

- API contract: `api/openapi.yaml`
- Data schema reference: `db/schema.sql`
- Architecture notes: `docs/architecture.md`
