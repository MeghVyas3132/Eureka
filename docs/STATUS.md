# 📦 Eureka — Shipped Status

> **Source of truth:** `prompt.md` (master spec). This document tracks *what is implemented and deployed* against that spec.
>
> Last updated: **2026-05-08**

---

## 1. Product flow (live)

```
Login
  → /upload   (auto-routed for users with no stores)
       Stores tab → Products tab → Sales tab
  → /dashboard
       Country → State → City → Locality → Store hierarchy tree
  → /stores/{id}        ← per-store landing
       "Generate AI Planogram" CTA
  → /stores/{id}/planogram/{pid}    ← Konva editor
       drag/drop · facing controls · confidence badge · data quality banner
       Save · Regenerate · Export (JPEG / PPTX) · Version history
```

Super-admin (separate flow): `/super-admin` → global stats cards · per-user usage vs quota · per-user limit editor.

---

## 2. Layer status (vs. `prompt.md` Section 4)

| Layer | Status | Notes |
|------|--------|------|
| **1. Auth** (JWT register / login / refresh) | ✅ Shipped | `backend/api/v1/auth.py`, role-based, approval workflow |
| **2. File Ingestion** (CSV / Excel / PDF + SKU dedup) | ✅ Shipped | `backend/ingestion/*` — file detection from bytes, column aliasing, validators, `rapidfuzz` deduplicator |
| **3. Data Normalisation** | ✅ Shipped | `backend/services/data_normalization.py` — category inference, dimension defaults |
| **3.5 Assortment Filter** | ✅ Shipped | `backend/services/assortment_filter.py` — sales-coverage / top-N / fallback; never returns 0 SKUs |
| **4. Store Intelligence** | ✅ Shipped | `backend/services/store_intelligence.py` — abbreviation expansion (RF, BLR…), PIN inference, parse confidence |
| **5. Planogram Engine** | ✅ Shipped | `backend/services/planogram_engine.py` — store-type rules, facings, confidence score, data quality warnings, canonical JSON |
| **6. Visual Editor (Konva)** | ✅ Shipped | `frontend/components/planogram/*` — `PlanogramCanvas`, `ProductBlock`, `FacingControls`, `ProductPanel`, `ConfidenceBadge`, `DataQualityBanner`, `RegenerateButton`, `ExportMenu` |
| **7. Export Engine (JPEG + PPTX)** | ✅ Shipped | `backend/services/export_service.py` + `GET /api/v1/planograms/{id}/export/{jpeg,pptx}` |

---

## 3. Frontend routes (live)

| Route | Purpose | Status |
|------|---------|--------|
| `/login`, `/register` | Auth | ✅ |
| `/upload` | **Data ingestion landing** — Stores / Products / Sales tabs with sample CSV downloads, ImportSummaryCard, history | ✅ New |
| `/dashboard` | **Hierarchy tree** (Country → State → City → Locality → Store) + selected-store data health | ✅ New |
| `/stores/{id}` | **Store landing page** — "Generate AI Planogram" CTA, product/sales readiness, planogram list | ✅ New |
| `/stores/{id}/planogram/{pid}` | Konva visual editor with confidence/quality UX + export | ✅ Shipped |
| `/stores/{id}/data` (alias `/store/{id}/data`) | Per-store data tabs | ✅ Shipped (preexisting) |
| `/products` | Product catalogue + import | ✅ Shipped (preexisting) |
| `/account` | Account settings | ✅ Shipped (preexisting) |
| `/super-admin` | Onboarding · Users · Limits + global stats cards · usage column | ✅ Updated |

Login redirect:
- Admin → `/super-admin`
- User with ≥ 1 store → `/dashboard`
- New user with 0 stores → `/upload`

---

## 4. API endpoints (live)

```
AUTH
  POST   /api/v1/auth/register
  POST   /api/v1/auth/login
  POST   /api/v1/auth/refresh

STORES
  POST   /api/v1/stores
  GET    /api/v1/stores
  GET    /api/v1/stores/hierarchy
  GET    /api/v1/stores/{id}
  PUT    /api/v1/stores/{id}
  DELETE /api/v1/stores/{id}
  POST   /api/v1/stores/import

PRODUCTS
  POST   /api/v1/products
  GET    /api/v1/products?filter=missing_dimensions|missing_category
  PUT    /api/v1/products/{id}
  DELETE /api/v1/products/{id}
  POST   /api/v1/products/import
  GET    /api/v1/products/import/history

SALES
  POST   /api/v1/sales
  GET    /api/v1/sales?store_id=
  PUT    /api/v1/sales/{id}
  DELETE /api/v1/sales/{id}
  POST   /api/v1/sales/import?store_id=&period_start=&period_end=
  GET    /api/v1/sales/import/history?store_id=

PLANOGRAMS
  POST   /api/v1/planograms/generate         ← quota-enforced
  POST   /api/v1/planograms/generate-all     ← quota-enforced
  GET    /api/v1/planograms?store_id=
  GET    /api/v1/planograms/{id}
  PUT    /api/v1/planograms/{id}             ← marks is_user_edited
  DELETE /api/v1/planograms/{id}
  GET    /api/v1/planograms/{id}/versions
  POST   /api/v1/planograms/{id}/rollback/{version_id}
  GET    /api/v1/planograms/{id}/export/jpeg ← Pillow
  GET    /api/v1/planograms/{id}/export/pptx ← python-pptx

ADMIN
  GET    /api/v1/admin/stats                 ← NEW: total users / stores / planograms / quota / utilisation
  GET    /api/v1/admin/users                 ← returns planogram_count + plan_limit per user
  PATCH  /api/v1/admin/users/{id}/plan-limit ← per-user override (limit / unlimited / tier-default)
  GET    /api/v1/admin/onboarding/requests
  PATCH  /api/v1/admin/onboarding/requests/{id}
  GET    /api/v1/admin/plan-limits
  PATCH  /api/v1/admin/plan-limits/{tier}
```

---

## 5. Quota / rate limiting

- **Per-user annual planogram limit** stored as `User.annual_planogram_limit_override` + `User.is_unlimited_override`. Tier defaults via `PlanLimit` table.
- **Resolution:** `services.plan_limit_service.resolve_user_plan_limit` — override always wins.
- **Enforcement:** `POST /api/v1/planograms/generate` and `/generate-all` call `_enforce_planogram_quota` and return `403 quota_exceeded` with `{limit, remaining}` payload when the user would exceed their cap.
- **Counting:** total = `SELECT COUNT(*) FROM planograms JOIN stores WHERE stores.user_id = :user_id`. Switched from the prior `Layout` count (which was the wrong concept).
- **Admin visibility:** `GET /api/v1/admin/stats` returns global totals + utilisation %; the Limits tab shows per-user `used / limit` with a color-coded bar.

---

## 6. Database

- PostgreSQL 16 (docker-compose service `postgres`)
- Async SQLAlchemy + asyncpg
- Alembic migrations in `backend/alembic/versions/` — latest: `20260504_0012_align_planogram_defaults.py`
- All required tables present: `users`, `stores`, `products`, `sales_data`, `planograms`, `planogram_versions`, `import_log`, plus the auxiliary `layouts/zones/shelves/placements` from earlier work
- All indexes per `prompt.md` Section 3.2

---

## 7. Tests

| Area | File | Status |
|------|------|--------|
| Auth + admin onboarding | `backend/tests/test_admin_users.py`, `test_admin_users.py::test_admin_can_list_users_with_planogram_counts` | ✅ Updated to count planograms |
| File ingestion | `backend/tests/ingestion/*` | ✅ Preexisting |
| SKU deduplicator | `backend/tests/ingestion/test_sku_deduplicator.py` | ✅ Preexisting |
| Assortment filter | `backend/tests/services/test_assortment_filter.py` | ✅ Preexisting |
| Store intelligence | `backend/tests/services/test_store_intelligence.py` | ✅ Preexisting |
| Planogram generate | `backend/tests/test_planogram_generate.py` | ✅ Preexisting |
| **Export service (JPEG + PPTX)** | `backend/tests/services/test_export_service.py` | ✅ **New — 8 tests, all passing** |

Run all backend service tests:
```bash
docker compose exec backend poetry run pytest tests/services/ -v
```

---

## 8. Deploy

Three-container stack via `docker-compose.yml`:
- `postgres` — Postgres 16 with persistent `pg_data` volume
- `backend` — FastAPI + Alembic auto-migrate on boot, `uvicorn --reload`
- `frontend` — Next.js 14 dev server with `next.config.js` configured to externalize `canvas` (so Konva stays client-only at build time)

```bash
docker compose up -d --build
docker compose ps
curl -s http://localhost:8000/openapi.json | head -c 400
open http://localhost:3000
```

---

## 9. Known caveats / out-of-scope (intentional)

Per `prompt.md` Section 19 these remain not built and won't be in MVP:
- ML models, computer vision, OCR for scanned PDFs
- Real-time POS / ERP / WMS connectors
- WebSocket collaboration
- Background job queues (Celery / Redis)
- Demand forecasting / stockout prediction
- A/B testing
- SKU merge UI (deduplicator currently flags only)
- Multi-sheet Excel parsing

Other deferred items that are nice-to-have:
- Frontend component tests for the Konva editor
- `/store/[id]/edit` is still a stub (the new `/stores/[id]` landing replaces its purpose)
- Backend `Layout` quota path predates the planogram-quota wire-up; `Layout` is a separate physical zoning feature and is not tied to planogram counting

---

## 10. Recent shipped work (this session)

1. Layer 7 export engine (Pillow JPEG, python-pptx 3-slide deck, low-confidence watermark) + 8 tests
2. Layer 6 visual editor (Konva canvas, ProductBlock, ProductPanel, FacingControls, ConfidenceBadge, DataQualityBanner, RegenerateButton, ExportMenu)
3. Zustand `planogramStore` with optimistic moveProduct / updateFacings / addProduct / removeProduct + shelf reflow
4. `next.config.js` webpack externalize for `canvas` (fixes Konva SSR build)
5. `/upload` data ingestion page (Stores / Products / Sales tabs, sample CSV download per tab)
6. `HierarchyTree` component + new `/dashboard` (Country → State → City → Locality)
7. `/stores/{id}` store landing page with "Generate AI Planogram" CTA + readiness/ inline quota error
8. Login redirect: new users → `/upload`, returning users → `/dashboard`, admins → `/super-admin`
9. Admin endpoints now count `Planogram` (not `Layout`) — schema field renamed `layout_count` → `planogram_count`
10. New `GET /api/v1/admin/stats` global metrics endpoint
11. Quota enforcement on `POST /api/v1/planograms/generate` and `/generate-all` (returns `403 quota_exceeded`)
12. Super-admin: 4 global metric cards above the tabs + per-user "Usage" column with progress bar in the Limits tab

Run `git log --oneline -20` for the underlying commits.
