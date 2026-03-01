# TreasureHunt.Tectrix2026 — Web Platform Blueprint

This repository now contains a production-ready technical blueprint for implementing the full Treasure Hunt system described in the requirements:

- Participant registration (email + roll uniqueness)
- Group formation with invitations and acceptance flow
- QR scanning and one-submission-per-team-per-QR validation
- Final QR winner logic with prerequisite completion checks
- Admin dashboard, game controls, and live monitoring
- Persistence across logout/login
- Responsive-first web architecture

## Repository structure

- `docs/architecture.md` — end-to-end system design and workflows
- `db/schema.sql` — relational database schema with constraints and indexes
- `api/openapi.yaml` — API contract (participant + admin endpoints)

## Next implementation step

Use this blueprint to generate and implement:

1. Backend service (Node/Express, Django, or FastAPI)
2. Frontend app (React/Vue/Next)
3. Realtime channel (WebSocket/SSE)
4. Auth/session and deployment configuration

