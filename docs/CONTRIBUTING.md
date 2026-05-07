# Contributing

Quick guide for working on Eureka. For the master spec read [`../prompt.md`](../prompt.md), for current shipped state read [`STATUS.md`](STATUS.md).

## Local setup

```bash
cp .env.example .env       # set SECRET_KEY (32+ chars)
make rebuild               # docker compose up -d --build
make ps
```

## Developing

- **Backend** (`backend/`): FastAPI, async SQLAlchemy. Code is mounted into the container — `uvicorn --reload` picks up edits live.
- **Frontend** (`frontend/`): Next.js dev server with hot reload. Konva must be loaded via `next/dynamic` with `ssr: false` (already wired in `app/stores/[id]/planogram/[pid]/page.tsx`).

## Commit conventions

Keep messages short, descriptive, and avoid numbers. Group changes by feature/area: one file per commit is fine; one feature per commit is better.

## Tests

```bash
make test-services   # service-level unit tests, no Postgres
make test            # full backend suite
make typecheck       # frontend tsc
```

When adding a new layer or service, add a test alongside it under `backend/tests/services/` or `backend/tests/`.

## Hard constraints

See [`../prompt.md` §18](../prompt.md). Most important:
- Always generate a planogram — never block on missing data
- Detect file format from bytes, never trust `Content-Type`
- All DB queries scoped by `user_id`
- Never use sync SQLAlchemy — `await db.execute(...)`
- SKU deduplicator flags only — never blocks imports

## Out of scope

See [`../prompt.md` §19](../prompt.md). Don't add ML models, real-time POS connectors, WebSocket collab, OCR for scanned PDFs, multi-sheet Excel parsing, or background job queues.
