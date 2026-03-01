# TreasureHunt.Tectrix2026 Architecture

## 1) High-Level Architecture

Users (mobile/laptop) access a responsive frontend that communicates with a backend API. The backend persists data in an RDBMS and object/file storage (if QR/media assets are needed), and drives the game engine + admin dashboard.

```text
Users -> Responsive Frontend -> Backend API -> DB + File Storage -> QR/Game Engine -> Admin Dashboard
```

## 2) Core Modules

- **Participant Auth & Registration**
  - Password-based login using hashed credentials (PBKDF2)
  - Registration enforces unique `(college_email, college_roll)`
  - Bearer session tokens with expiry store authenticated participant/admin context

- **Group Management**
  - Group creation by registered participant only
  - Group size hard limits: min 2, max 4 (including creator)
  - One participant can belong to only one active group
  - Invitation + acceptance workflow before membership is finalized

- **QR Scanning & Submission**
  - Scan endpoint validates QR token and game state
  - Submission captures team ID, QR, answer, explanation, member, timestamp
  - Unique constraint prevents duplicate submit by same team on same QR

- **Game End / Final QR**
  - Admin flags one QR as final
  - A team can only complete final QR if prerequisite rule is satisfied
  - On success, store completion and return winner message

- **Admin Control Panel**
  - Dashboard counters and latest activity
  - Participant and team drill-down views
  - Live submission monitor
  - Pause/resume/close game, disqualify team, set final QR, edit QR clues
  - Broadcast messages (SMS or in-app)

## 3) Business Rules

1. `college_email` and `college_roll` are globally unique.
2. A participant must register before group operations.
3. Participant can be in **at most one** non-disbanded group.
4. Group member count must stay in `[2,4]` before game participation.
5. One team can submit a QR answer only once.
6. Final QR submission requires precondition (e.g., solved/submitted all mandatory non-final QRs).
7. Logout never deletes progress; sessions only end authentication state.

## 4) Realtime Data

Use WebSocket/SSE channels for:
- admin dashboard metrics refresh
- live submission monitor
- broadcast announcements

## 5) Suggested Non-Functional Requirements

- Mobile-first responsive UI, camera permission prompts optimized
- Low-bandwidth payload design (compressed JSON, pagination)
- Audit logs for admin actions and moderation
- Idempotent endpoints for invitation acceptance and submissions
- Rate limiting on QR scan/submit endpoints

## 6) Security

- CSRF-safe cookie sessions or short-lived JWT + refresh token
- Role-based access (`participant`, `admin`)
- Input validation and SQL-injection-safe ORM/queries
- Server-side enforcement for all constraints (never frontend-only)
- Signed QR payload or random nonce token to reduce forgery/replay

## 7) Deployment Shape

- Frontend: static hosting or containerized app
- Backend: container + autoscaling instance group
- DB: PostgreSQL managed service
- Cache/message bus (optional): Redis for live counters/queues
- Observability: structured logs + metrics + alerts

