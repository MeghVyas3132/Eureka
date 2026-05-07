# 🚀 Eureka

> **Self-serve retail planogram platform.** Upload → Structure → Generate → Edit → Export.
>
> Status: **MVP shipped.** See [docs/STATUS.md](docs/STATUS.md) for the full shipped-vs-spec log.

```
Messy retail data (CSV / Excel / PDF)
         ↓
  Normalised product + sales + store data
         ↓
  Filtered assortment per store
         ↓
  Auto-generated planograms with confidence scoring
         ↓
  User edits in visual editor
         ↓
  Export as JPEG / PPTX
```

**Primary success metric:** user uploads a file → sees a usable planogram → within 2 minutes.

---

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router, TypeScript) |
| Canvas / Editor | Konva + react-konva |
| State | Zustand · TanStack React Query · Axios |
| Styling | Tailwind |
| Backend | FastAPI (async) |
| ORM | SQLAlchemy (asyncpg) + Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT (`python-jose` + `passlib[bcrypt]`) |
| Parsing | `pandas`, `openpyxl`, `pdfplumber`, `chardet`, `python-magic` |
| Dedup | `rapidfuzz==3.9.7` |
| Export | `Pillow` (JPEG) · `python-pptx` (PowerPoint) |
| Storage | AWS S3 in prod / local filesystem in dev |
| Deploy | Docker + docker-compose |

The full implementation contract is in [`prompt.md`](prompt.md). Older PRDs in `docs/` describe an earlier "store canvas" pivot — the current product follows `prompt.md` + `docs/STATUS.md`.

---

## Quickstart (local dev)

```bash
git clone <repo>
cd Eureka
cp .env.example .env       # fill in SECRET_KEY (32+ chars)
docker compose up -d --build
docker compose ps          # wait for all 3 to be Up

# Frontend → http://localhost:3000
# Backend  → http://localhost:8000  (OpenAPI: /openapi.json, docs: /docs)
# Postgres → localhost:5432  (eureka / eureka / eureka_db)
```

To reset everything: see [`docs/dev-reset.md`](docs/dev-reset.md).

---

## End-to-end product flow

```
Login
  → /upload          (auto-redirected for users with zero stores)
       Stores tab → Products tab → Sales tab
  → /dashboard
       Country → State → City → Locality → Store hierarchy tree
  → /stores/{id}                 ← per-store landing
       "Generate AI Planogram" CTA
  → /stores/{id}/planogram/{pid} ← Konva editor
       drag/drop · facings · confidence badge · data-quality warnings
       Save · Regenerate (with overwrite warning) · Export ▼ (JPEG / PPTX)
       Version history + rollback
```

Super-admin (separate route, role-gated): global stats cards · per-user planogram usage vs quota · per-user limit editor (tier default / unlimited / custom).

---

## What's built

| Layer (per `prompt.md` §4) | Status |
|----|----|
| 1. Auth (JWT, register/login/refresh, role + approval) | ✅ |
| 2. File Ingestion (CSV / Excel / PDF + SKU dedup) | ✅ |
| 3. Data Normalisation (category inference, dimension defaults) | ✅ |
| 3.5. Assortment Filter (sales-coverage / top-N / fallback) | ✅ |
| 4. Store Intelligence Engine (abbreviation expansion, PIN lookup, parse confidence) | ✅ |
| 5. Planogram Engine (store-type rules, facings, confidence, data-quality warnings) | ✅ |
| 6. Visual Editor (Konva canvas + drag-drop + facing controls + confidence/quality UX) | ✅ |
| 7. Export Engine (JPEG via Pillow + PPTX via python-pptx) | ✅ |

See [docs/STATUS.md](docs/STATUS.md) §2 for the file-by-file breakdown and §10 for the latest shipped work.

---

## Repo layout

```
.
├── backend/
│   ├── api/v1/                 — auth, stores, products, sales, planograms, layouts, admin_*
│   ├── services/               — planogram_engine, store_intelligence, assortment_filter,
│   │                             data_normalization, export_service (JPEG + PPTX), …
│   ├── ingestion/              — file_detector, parsers, validators, sku_deduplicator
│   ├── models/                 — SQLAlchemy models (UUID PKs, multi-tenant scoped)
│   ├── alembic/versions/       — migrations
│   └── tests/                  — pytest (unit + httpx ASGI integration)
│
├── frontend/
│   ├── app/                    — Next.js App Router routes
│   │   ├── (auth)/login/, /register
│   │   ├── upload/             — Stores / Products / Sales tabs (post-login landing for new users)
│   │   ├── dashboard/          — hierarchy tree + selected-store data health
│   │   ├── stores/[id]/        — store landing with "Generate AI Planogram" CTA
│   │   ├── stores/[id]/planogram/[pid]/ — Konva editor
│   │   └── super-admin/        — global stats + user/limit management
│   ├── components/
│   │   ├── planogram/          — PlanogramCanvas, ProductBlock, ProductPanel, FacingControls,
│   │   │                         ConfidenceBadge, DataQualityBanner, RegenerateButton, ExportMenu
│   │   ├── dashboard/          — HierarchyTree, DataHealthWidget
│   │   ├── ingestion/, products/, sales/, stores/  — importers + ImportSummaryCard
│   │   └── auth/, layout/      — auxiliary
│   ├── store/                  — Zustand stores (auth, planogramStore, canvasStore)
│   └── lib/                    — api client, planogramRouting helpers
│
├── docs/
│   ├── STATUS.md               ← canonical shipped log (READ THIS)
│   ├── PRODUCT_REQUIREMENTS_DOCUMENT.md
│   ├── MVP_PRODUCT_REQUIREMENTS_DOCUMENT_v2.md
│   ├── MVP_TECHNICAL_REQUIREMENTS_DOCUMENT_v2.md
│   ├── EUREKA_MVP_IMPLEMENTATION_PLAN.md
│   ├── readme-mvp-v2.md
│   └── dev-reset.md
│
├── prompt.md                   — master spec (source-of-truth)
└── docker-compose.yml
```

---

## Quota / rate limits

- Per-tier defaults via `PlanLimit` table; per-user overrides via `User.annual_planogram_limit_override` + `is_unlimited_override` (override always wins).
- Enforced at `POST /api/v1/planograms/generate` and `/generate-all` — returns `403 quota_exceeded` with `{limit, remaining}` payload.
- Super-admin sees global utilisation in `/api/v1/admin/stats`, and per-user `used / limit` in the Limits tab.

---

## Tests

```bash
# Backend unit + service tests (no DB required)
docker compose exec backend poetry run pytest tests/services/ -v

# Full backend test suite (requires Postgres reachable)
docker compose exec backend poetry run pytest -v

# Frontend type-check + production build
docker compose exec frontend node_modules/.bin/tsc --noEmit
docker compose exec frontend npm run build
```

---

## How to test the product

A complete step-by-step UI test plan is in [docs/STATUS.md](docs/STATUS.md). Short version:

1. Register at `/register`, get approved by admin (or seed admin via the existing fixture)
2. Login → land on `/upload` (auto-redirected for new users)
3. Stores tab → upload sample CSV → Products tab → upload → Sales tab → upload
4. "Go to Dashboard →" → see the hierarchy tree → click a store
5. On the store landing page, click "Generate AI Planogram"
6. Drag a SKU between shelves, hit + on facings, click Save
7. Click **Export ▼** → JPEG or PPTX → file downloads
8. Log in as the seeded admin (`admin@aexiz.com / qwerty123`) → `/super-admin` → see global metric cards + per-user usage column

---

## Hard constraints (per `prompt.md` §18)

1. Never block planogram generation due to missing data — use defaults
2. Never overwrite `is_user_edited = true` planograms automatically — always warn first
3. Never trust `Content-Type` — detect format from bytes via `python-magic`
4. Never make outbound HTTP calls from the backend
5. Never abort imports because of bad rows — partial commit + log
6. Never use synchronous SQLAlchemy — `await db.execute(...)` everywhere
7. Never hardcode secrets — env-only
8. All queries scoped by `user_id` for multi-tenant isolation
9. SKU deduplicator flags only — never blocks
10. Assortment filter never returns 0 SKUs

---

## Out-of-scope (per `prompt.md` §19)

ML, real-time connectors, WebSocket collab, computer vision, background job queues, demand forecasting, A/B testing, SKU merge UI, OCR for scanned PDFs, multi-sheet Excel parsing.
