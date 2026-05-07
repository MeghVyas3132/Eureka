# 🛠️ EUREKA – MVP IMPLEMENTATION PLAN

> Based on: `MVP_PRD_v2` + `MVP_TRD_v2` + `readme-mvp-v2`
> Stack: **Next.js · FastAPI · SQLAlchemy · Alembic · PostgreSQL**
> MVP Loop (original): `Design → Product Placement → CSV Import → Analytics`

> ⚠️ **Status note (updated 2026-05-08):** This is the **original sprint plan** for the canvas-first MVP. The product later pivoted to the **planogram platform** specified in [`prompt.md`](prompt.md) (Upload → Structure → Generate → Edit → Export). The shipped product matches that pivot. For what's currently built and deployed, read [`docs/STATUS.md`](docs/STATUS.md) and the root [`readme.md`](readme.md).

---

## 🚢 SHIPPED STATUS SNAPSHOT (2026-05-08)

The **canvas-first MVP loop** in this plan was superseded by the planogram platform. The table below maps original sprints to current shipped scope.

| Original sprint | Original goal | Current status |
|---|---|---|
| Sprint 1 — Foundation & Auth | JWT auth, register/login/refresh, protected dashboard | ✅ **Shipped** — also adds role-based access, admin approval workflow, super-admin |
| Sprint 2 — Store / Layout / Zone / Shelf | Store CRUD + zone/shelf canvas data model | ✅ **Shipped** for Stores; Layout/Zone/Shelf models exist but the UI is no longer the primary flow (replaced by planogram engine) |
| Sprint 3 — Canvas Layout Editor (Konva) | Drag/drop store-floorplan editor | ⚠️ **Pivoted** — Konva editor now powers the **planogram editor** (`/stores/{id}/planogram/{pid}`), not store-floor-plan editing |
| Sprint 4 — Products + Placement | CSV import, drag products to shelves, facings | ✅ **Shipped** — products + sales + stores all import via CSV/Excel/PDF (Layer 2). Drag/facings/placement live on the planogram canvas |
| Sprint 5 — Sales + Analytics Dashboard | Sales CSV + 5 analytics metrics | ⚠️ **Re-scoped** — sales CSV ingest shipped; "5 analytics metrics" replaced by the **confidence score + data-quality warnings** surfaced on the planogram editor and the per-store **DataHealthWidget** on the dashboard |

### Net delta from original plan

**Added beyond plan:**
- Layer 3.5 Assortment Filter (`backend/services/assortment_filter.py`)
- Layer 4 Store Intelligence Engine (`backend/services/store_intelligence.py`)
- Layer 5 Planogram Engine with store-type rules + confidence scoring (`backend/services/planogram_engine.py`)
- Layer 7 Export Engine — JPEG (Pillow) + PPTX (python-pptx) (`backend/services/export_service.py`)
- Hierarchical store dashboard (Country → State → City → Locality)
- Per-store landing page with "Generate AI Planogram" CTA
- Auto-redirect on login: new users → `/upload`, returning → `/dashboard`, admins → `/super-admin`
- Per-user planogram quota enforcement at generate time
- Admin global stats endpoint (`GET /api/v1/admin/stats`) + super-admin metric cards & per-user usage column
- SKU fuzzy deduplicator (`rapidfuzz`)

**Out-of-scope vs original plan:**
- Standalone analytics dashboard with the 5 metrics (heatmap, sales-by-zone, etc.) — replaced by confidence + data-quality UX
- Store floor-plan canvas editor — superseded by the planogram editor
- Standalone shelf editor side panel

The full file-by-file shipped log lives in [`docs/STATUS.md`](docs/STATUS.md).

---

## 📋 OVERVIEW

The MVP is broken into **5 sequential sprints** of roughly 1–2 weeks each. Each sprint produces a working, testable slice of the system — nothing is left as scaffolding. The order is infrastructure-first, then data models, then feature-by-feature from the canvas outward.

**Total estimated duration:** 8–10 weeks (solo or small team)

---

## 🗂️ PROJECT STRUCTURE (target)

```
eureka/
├── frontend/                          # React.js 18 (Vite SPA)
│   ├── index.html                     # Vite entry point
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx                   # React root, ReactDOM.createRoot
│   │   ├── App.tsx                    # React Router v6 route definitions
│   │   ├── pages/                    # src/pages/ route components
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   └── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── store/
│   │   │   │   ├── LayoutPage.tsx
│   │   │   │   ├── AnalyticsPage.tsx
│   │   │   │   └── DataPage.tsx
│   │   │   └── ProductsPage.tsx
│   │   ├── components/
│   │   │   ├── canvas/                # Konva 2D layout editor
│   │   │   ├── planogram/             # Konva planogram editor + Three.js 3D view
│   │   │   ├── analytics/             # Charts + metric cards
│   │   │   ├── products/              # Product panel + CSV importer
│   │   │   └── sales/                 # Sales entry + CSV importer
│   │   ├── router/
│   │   │   └── ProtectedRoute.tsx     # Auth guard (replaces framework middleware)
│   │   ├── store/                     # Zustand state slices
│   │   └── lib/                       # Axios instance, utils
│
├── backend/                           # FastAPI
│   ├── main.py
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── stores.py
│   │   ├── layouts.py
│   │   ├── zones.py
│   │   ├── shelves.py
│   │   ├── products.py
│   │   ├── products_import.py
│   │   ├── placements.py
│   │   ├── sales.py
│   │   ├── sales_import.py
│   │   └── analytics.py
│   ├── models/                        # SQLAlchemy ORM models
│   ├── schemas/                       # Pydantic request/response
│   ├── services/
│   │   ├── layout_service.py
│   │   ├── product_service.py
│   │   ├── placement_service.py
│   │   ├── sales_service.py
│   │   ├── csv_ingestion_service.py
│   │   └── analytics_service.py
│   ├── db/
│   │   ├── session.py                 # Async SQLAlchemy session
│   │   └── base.py                    # Declarative base
│   └── alembic/
│       ├── env.py
│       └── versions/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚦 SPRINT BREAKDOWN

---

### ✅ SPRINT 1 — Foundation & Auth
**Duration:** ~1 week
**Goal:** Working monorepo, DB running, auth functional end-to-end

#### Backend Tasks
- [ ] Init FastAPI project with folder structure
- [ ] Configure async SQLAlchemy (`asyncpg` driver) + session factory in `db/session.py`
- [ ] Configure Alembic (`alembic init`, link to `db/base.py`)
- [ ] Write SQLAlchemy model: `User` (id, email, hashed_password, role, created_at)
- [ ] Write Alembic migration: `001_create_users_table`
- [ ] Implement `/api/v1/auth` routes:
  - `POST /auth/register` — create user, hash password with `passlib[bcrypt]`
  - `POST /auth/login` — verify credentials, return JWT access + refresh token
  - `POST /auth/refresh` — rotate access token from refresh token
- [ ] JWT middleware: `get_current_user` dependency using `python-jose`
- [ ] RBAC dependency: `require_role(["admin", "merchandiser"])` FastAPI `Depends`
- [ ] Write pytest fixtures: test DB setup, test user factory
- [ ] Unit tests: register, login, token refresh, invalid credentials

#### Frontend Tasks
- [ ] Init React 18 + Vite project (TypeScript, Tailwind CSS)
      `npm create vite@latest frontend -- --template react-ts`
- [ ] Install: `react-router-dom`, `zustand`, `axios`, `@tanstack/react-query`,
               `konva`, `react-konva`, `three`, `@react-three/fiber`,
               `tailwindcss`, `react-dropzone`, `date-fns`
- [ ] Configure Vite (`vite.config.ts`): proxy `/api` → backend on port 8000
- [ ] Create `src/pages/auth/LoginPage.tsx` — login form
- [ ] Create `src/pages/auth/RegisterPage.tsx` — register form
- [ ] Create `src/App.tsx` — `<BrowserRouter>` with all `<Route>` definitions
- [ ] Create `src/router/ProtectedRoute.tsx` — reads JWT from `authStore`,
      redirects to `/` if unauthenticated
- [ ] Zustand `authStore`: stores JWT token, user object, logout action
- [ ] Axios instance in `src/lib/api.ts`: auto-attaches Bearer token, handles 401 → redirect
- [ ] Env var: `VITE_API_URL` in `.env` (replaces legacy public API URL prefix)

#### Infrastructure
- [ ] `docker-compose.yml`: services for `postgres`, `backend`, `frontend`
- [ ] `.env.example` with all required vars: `DATABASE_URL`, `SECRET_KEY`, `VITE_API_URL`, `S3_*`, etc.
- [ ] `alembic upgrade head` runs in Docker entrypoint

**Sprint 1 exit criteria:** User can register, log in, receive JWT, and access a protected `/dashboard` page.

---

### ✅ SPRINT 2 — Store + Layout + Zone + Shelf Data Layer
**Duration:** ~1.5 weeks
**Goal:** Full CRUD for stores, layouts, zones, shelves — with versioning

#### Backend Tasks

**Models (SQLAlchemy):**
- [ ] `Store` — id, user_id (FK), name, width_m, height_m, store_type, created_at
- [ ] `Layout` — id, store_id (FK), name, created_at, updated_at
- [ ] `LayoutVersion` — id, layout_id (FK), version_number, snapshot_json (JSONB), created_at
- [ ] `Zone` — id, layout_id (FK), name, zone_type, x, y, width, height
- [ ] `Shelf` — id, zone_id (FK), x, y, width_cm, height_cm, num_rows

**Alembic migrations:**
- [ ] `002_create_stores_table`
- [ ] `003_create_layouts_and_versions`
- [ ] `004_create_zones_and_shelves`

**API routes:**
- [ ] `POST /api/v1/stores` — create store
- [ ] `GET /api/v1/stores` — list stores (scoped to current user)
- [ ] `GET /api/v1/stores/{store_id}` — get store detail
- [ ] `PUT /api/v1/stores/{store_id}` — update store
- [ ] `DELETE /api/v1/stores/{store_id}` — delete store
- [ ] `POST /api/v1/layouts` — create layout for a store
- [ ] `GET /api/v1/layouts/{layout_id}` — get layout with all zones/shelves
- [ ] `PUT /api/v1/layouts/{layout_id}` — save layout (triggers version snapshot)
- [ ] `GET /api/v1/layouts/{layout_id}/versions` — list versions
- [ ] `POST /api/v1/layouts/{layout_id}/rollback/{version_id}` — restore version
- [ ] `POST /api/v1/zones` — create zone in layout
- [ ] `PUT /api/v1/zones/{zone_id}` — update zone (position, dimensions, name)
- [ ] `DELETE /api/v1/zones/{zone_id}`
- [ ] `POST /api/v1/shelves` — create shelf in zone
- [ ] `PUT /api/v1/shelves/{shelf_id}` — update shelf
- [ ] `DELETE /api/v1/shelves/{shelf_id}`

**Layout Service logic:**
- [ ] `save_layout_snapshot()` — serialises zones + shelves + placements to JSONB and writes to `layout_versions`
- [ ] `rollback_layout(version_id)` — restores zones/shelves from snapshot

**Tests:**
- [ ] CRUD tests for all endpoints (httpx + pytest)
- [ ] Version snapshot test: save → mutate → rollback → assert original state restored
- [ ] Multi-tenancy test: user A cannot access store of user B

#### Frontend Tasks
- [ ] `/dashboard` page — store list, "New Store" button
- [ ] `NewStoreModal` — form: name, width_m, height_m, store_type (select: supermarket/convenience/specialty)
- [ ] `StoreCard` component — shows store name, type, last updated, "Open Layout" button
- [ ] `/store/:id/layout` page shell — renders top nav, sidebar, canvas area placeholder

**Sprint 2 exit criteria:** User can create a store, create a layout, and the backend correctly versions every save.

---

### ✅ SPRINT 3 — Canvas Layout Editor (Core UI)
**Duration:** ~2 weeks
**Goal:** Fully working drag-and-drop canvas. Zones and shelves can be created, moved, resized, saved.

#### Frontend Tasks (Konva.js)

**Canvas engine setup:**
- [ ] `LayoutCanvas.tsx` — Konva `Stage` + `Layer`; dimensions match store width/height (scaled to viewport)
- [ ] `ThreeDViewToggle.tsx` — button to switch between Konva 2D view and Three.js 3D view
      (Three.js view is a placeholder in MVP — renders a basic 3D shelf frame only)
      Full 3D planogram rendering is Phase 2.
- [ ] Grid overlay — dotted grid lines at configurable unit (cm-based, scaled to px)
- [ ] Snap-to-grid logic — all object positions rounded to nearest grid unit on drag end
- [ ] Zoom + pan — mouse wheel zoom, middle-click pan

**Zone interaction:**
- [ ] `ZoneShape.tsx` — Konva `Rect` for each zone; colour-coded by `zone_type`
- [ ] Zone sidebar panel — "Add Zone" button with type selector (aisle, entrance, checkout, department)
- [ ] Drag zone from sidebar → drops onto canvas as a new zone (calls `POST /api/v1/zones`)
- [ ] Click zone → show resize handles (Konva `Transformer`)
- [ ] Drag zone on canvas → update position (debounced `PUT /api/v1/zones/{id}`)
- [ ] Right-click zone → context menu: Rename, Delete

**Shelf interaction:**
- [ ] `ShelfShape.tsx` — rendered inside a zone as a narrower Rect
- [ ] "Add Shelf" button inside zone context → drops shelf at zone origin
- [ ] Drag shelf within its parent zone
- [ ] Click shelf → opens `ShelfEditor` side panel (Sprint 4)

**Templates:**
- [ ] `TemplateSelector.tsx` — modal shown on new layout creation
- [ ] 3 templates: Supermarket (grid aisles), Convenience (perimeter shelves), Specialty (freeform zones)
- [ ] Template applies a preset JSON of zones/shelves via `POST /api/v1/layouts` with initial state

**Save / version:**
- [ ] "Save" button → `PUT /api/v1/layouts/{id}` → triggers backend snapshot
- [ ] `VersionHistoryPanel.tsx` — drawer showing last N versions with timestamps, "Restore" button

**Zustand canvas store:**
```
canvasStore:
  - zones: Zone[]
  - shelves: Shelf[]
  - selectedZoneId: string | null
  - selectedShelfId: string | null
  - setZones / updateZone / deleteZone
  - setShelves / updateShelf / deleteShelf
```

#### Backend Tasks
- [ ] Validate zone bounds — zone must fit within store dimensions (backend check)
- [ ] Validate shelf bounds — shelf must fit within parent zone

**Sprint 3 exit criteria:** User can build a full store floor plan from scratch or template, with zones and shelves that snap to grid and persist after page refresh.

---

### ✅ SPRINT 4 — Products + Placement
**Duration:** ~1.5 weeks
**Goal:** Product master data, CSV import, drag products onto shelves with size-aware placement

#### Backend Tasks

**Models:**
- [ ] `Product` — id, user_id (FK), sku (unique per user), name, brand, category, width_cm, height_cm, depth_cm, price, image_url, created_at
- [ ] `Placement` — id, shelf_id (FK), product_id (FK), position_x, facing_count

**Alembic migrations:**
- [ ] `005_create_products`
- [ ] `006_create_placements`

**API routes:**
- [ ] `POST /api/v1/products` — create product (manual)
- [ ] `GET /api/v1/products` — list (filter by category, brand, search)
- [ ] `PUT /api/v1/products/{id}` — update
- [ ] `DELETE /api/v1/products/{id}`
- [ ] `POST /api/v1/products/import` — CSV bulk import
- [ ] `POST /api/v1/placements` — place product on shelf
- [ ] `GET /api/v1/placements?shelf_id=` — get placements for a shelf
- [ ] `PUT /api/v1/placements/{id}` — update position/facing count
- [ ] `DELETE /api/v1/placements/{id}` — remove product from shelf

**CSV Ingestion Service (`csv_ingestion_service.py`):**
- [ ] Parse CSV with `csv.DictReader`
- [ ] Validate: `sku` and `name` required; numeric fields must be valid numbers
- [ ] Upsert logic: duplicate SKU → update existing record (not duplicate)
- [ ] Bulk insert via `SQLAlchemy bulk_insert_mappings`
- [ ] Return: `{ total_rows, success, skipped, errors: [{row, reason}] }`
- [ ] Archive raw CSV to S3 + log to `csv_import_log` table

**Placement validation:**
- [ ] Shelf capacity check: sum of (product.width_cm × facing_count) ≤ shelf.width_cm
- [ ] Reject placement if over capacity; return 400 with capacity detail

**Tests:**
- [ ] CSV import: valid file, malformed rows, missing required fields, duplicate SKUs, empty file, 10 MB+ file
- [ ] Placement capacity validation tests
- [ ] Multi-tenancy: products scoped to `user_id`

#### Frontend Tasks

**Product Panel (sidebar on layout canvas):**
- [ ] `ProductPanel.tsx` — searchable list of all user's products
- [ ] Filter by category, brand
- [ ] "Add Product" button → manual creation form modal
- [ ] "Import CSV" button → `ProductImporter.tsx`

**Product Importer:**
- [ ] `ProductImporter.tsx` — drag-and-drop or file picker for CSV
- [ ] Preview: show first 5 rows before confirming import
- [ ] After import: show summary card (success / skipped / errors)

**Shelf Editor:**
- [ ] `ShelfEditor.tsx` — opens in right sidebar when a shelf is clicked
- [ ] Shows shelf as horizontal row; each product rendered as a coloured block proportional to `width_cm`
- [ ] Drag product from `ProductPanel` onto a shelf row → calls `POST /api/v1/placements`
- [ ] Facing count `+/-` controls per product on shelf
- [ ] Product overflow warning if shelf capacity exceeded
- [ ] Remove product (×) button per placement

**Zustand product store:**
```
productStore:
  - products: Product[]
  - placements: Record<shelfId, Placement[]>
  - fetchProducts / addProduct / importProducts
  - fetchPlacements / addPlacement / updatePlacement / removePlacement
```

**Sprint 4 exit criteria:** User can import products via CSV, drag them onto shelves, see size-accurate placement, and adjust facings — all persisted to DB.

---

### ✅ SPRINT 5 — Sales Data Import + Analytics Dashboard
**Duration:** ~1.5 weeks
**Goal:** Sales data enters via CSV or manual entry; analytics dashboard computes and displays all MVP metrics

#### Backend Tasks

**Models:**
- [ ] `SalesData` — id, store_id (FK), sku, period_start, period_end, units_sold, revenue, ingestion_method, created_at
- [ ] `CsvImportLog` — id, store_id (FK), import_type, filename, total_rows, success_count, error_count, imported_at, imported_by (FK users)

**Alembic migrations:**
- [ ] `007_create_sales_data`
- [ ] `008_create_csv_import_log`

**API routes:**
- [ ] `POST /api/v1/sales` — manual entry of a single SKU sales record
- [ ] `GET /api/v1/sales?store_id=` — list sales records for a store
- [ ] `PUT /api/v1/sales/{id}` — edit a manual entry
- [ ] `DELETE /api/v1/sales/{id}`
- [ ] `POST /api/v1/sales/import` — multipart CSV upload

**Sales CSV Import:**
- [ ] Accepts columns: `sku, units_sold, revenue`
- [ ] `period_start` + `period_end` passed as query params at upload time (not per-row)
- [ ] Unmatched SKUs flagged in summary (not rejected — they're stored with a `matched: false` flag for reference)
- [ ] Upsert: same store + SKU + period → overwrite

**Analytics Service (`analytics_service.py`):**

All computations are pure SQL/ORM queries over `sales_data` + `placements` + `zones` + `shelves`:

```python
async def get_sales_per_shelf(layout_id: UUID) -> list[ShelfSalesResult]:
    # Join placements → sales_data on sku, aggregate revenue per shelf_id

async def get_sales_per_zone(layout_id: UUID) -> list[ZoneSalesResult]:
    # Aggregate shelf results up to zone level

async def get_revenue_per_sqft(layout_id: UUID) -> list[ZoneRevenuePerSqFt]:
    # zone_revenue / (zone.width × zone.height converted to sqft)

async def get_sku_ranking(store_id: UUID) -> list[SkuRankResult]:
    # Sort sales_data by revenue DESC, join product name

async def get_layout_performance_score(layout_id: UUID) -> float:
    # Composite: (space_utilisation_ratio × 0.5) + (sales_distribution_score × 0.5)
    # Space utilisation = sum(product widths × facings) / sum(shelf widths)
    # Sales distribution = coefficient of variation of revenue across zones (lower = more even = better)

async def get_data_freshness(store_id: UUID) -> datetime | None:
    # MAX(created_at) FROM sales_data WHERE store_id = ?
```

**PostgreSQL indexes to add in migration:**
```sql
CREATE INDEX idx_sales_store_id ON sales_data(store_id);
CREATE INDEX idx_sales_sku ON sales_data(sku);
CREATE INDEX idx_placements_shelf_id ON placements(shelf_id);
CREATE INDEX idx_zones_layout_id ON zones(layout_id);
```

**Analytics API:**
- [ ] `GET /api/v1/analytics/{layout_id}/overview` — returns all metrics in a single response payload
- [ ] `GET /api/v1/analytics/{layout_id}/shelves` — per-shelf breakdown
- [ ] `GET /api/v1/analytics/{layout_id}/zones` — per-zone breakdown
- [ ] `GET /api/v1/analytics/{layout_id}/skus` — SKU ranking table

#### Frontend Tasks

**Sales Data Page (`/store/:id/data`):**
- [ ] `SalesDataImporter.tsx` — CSV upload with period date range picker
- [ ] `ManualSalesEntry.tsx` — form: SKU dropdown (from known products), units, revenue, period
- [ ] Import history table — previous imports with timestamp, row counts, status
- [ ] `DataFreshnessIndicator.tsx` — shows "Data as of [date]" badge on all analytics views

**Analytics Dashboard (`/store/:id/analytics`):**
- [ ] `LayoutPerformanceScore.tsx` — large score card (0–100), colour-coded
- [ ] `ZoneSalesChart.tsx` — bar chart of revenue per zone (Recharts or Chart.js)
- [ ] `ShelfSalesHeatGrid.tsx` — visual grid of shelves colour-coded high/medium/low revenue
- [ ] `SkuRankingTable.tsx` — sortable table: rank, SKU, product name, units sold, revenue
- [ ] `RevenuePerSqFtCard.tsx` — zone-level table with flag for underperforming zones
- [ ] `DataFreshnessIndicator.tsx` — shown in page header: "Last updated: Jan 31, 2025 · Not live"
- [ ] Empty state — shown if no sales data uploaded yet, with "Import Sales Data" CTA

**Zustand analytics store:**
```
analyticsStore:
  - overview: AnalyticsOverview | null
  - dataFreshness: string | null
  - isLoading: boolean
  - fetchAnalytics(layoutId)
```

**Sprint 5 exit criteria:** User can upload a sales CSV, see all 5 analytics metrics rendered on the dashboard, with a "Last updated" timestamp displayed prominently. Full E2E test passes: create layout → place products → import CSV → view analytics.

---

## 🧪 TESTING PLAN

| Level | Tool | What to test |
|-------|------|-------------|
| Unit (backend) | `pytest` | Analytics computations, CSV parser, placement capacity logic, auth token logic |
| API integration | `httpx` + `pytest` | All 30+ endpoints; auth guards; tenant isolation |
| CSV edge cases | pytest fixtures | Valid, malformed, empty, over 10 MB, missing required columns, duplicate SKUs |
| DB migrations | Alembic + test DB | Each migration applies and rolls back cleanly |
| Frontend components | Vitest + React Testing Library | Canvas interactions, product panel, importer, analytics cards |
| E2E | Playwright | Full user flow: register → create store → layout → place products → import CSV → analytics |

---

## 🚀 DEPLOYMENT CHECKLIST

**Dev:**
- [ ] `docker-compose up` starts postgres + backend + frontend
- [ ] Alembic auto-runs on backend startup
- [ ] Seed script creates demo user + sample store

**Production (AWS):**
- [ ] Backend: ECS Fargate (Docker image)
- [ ] Frontend: AWS S3 + CloudFront (Vite builds to static dist/ — no server needed)
      OR Nginx container on ECS serving the built dist/ folder
- [ ] Database: AWS RDS PostgreSQL (Multi-AZ)
- [ ] Storage: S3 bucket (product images + CSV archives) + CloudFront
- [ ] Secrets: AWS Secrets Manager
- [ ] CI/CD: GitHub Actions → run tests → build Docker → run Alembic → deploy

**GitHub Actions workflow:**
```yaml
on: push to main
steps:
  1. pytest (backend)
  2. vitest (frontend)
  3. docker build
  4. alembic upgrade head (against staging RDS)
  5. deploy to ECS
  6. playwright E2E against staging
```

---

## 📦 DEPENDENCIES (Key Packages)

**Backend (`requirements.txt`):**
```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
pydantic[email]
python-jose[cryptography]
passlib[bcrypt]
python-multipart          # file upload
pandas                    # CSV parsing (or csv stdlib)
boto3                     # S3
pytest
httpx
pytest-asyncio
```

**Frontend (`package.json`):**
```
react
react-dom
react-router-dom          # client-side routing (replaces framework routing)
konva
react-konva               # 2D canvas — layout editor and planogram editor
three                     # 3D canvas — future 3D planogram view
@react-three/fiber        # React wrapper for Three.js
zustand
axios
@tanstack/react-query
tailwindcss
recharts                  # analytics charts
react-dropzone            # CSV drag-and-drop upload
date-fns                  # date formatting for data freshness
vite                      # build tool (dev + production)
@vitejs/plugin-react      # Vite React plugin
vitest                    # unit + component testing (Vite-native)
@testing-library/react
playwright                # E2E testing
```

---

## 🔢 API ENDPOINT REFERENCE (Complete MVP)

```
AUTH
  POST   /api/v1/auth/register
  POST   /api/v1/auth/login
  POST   /api/v1/auth/refresh

STORES
  POST   /api/v1/stores
  GET    /api/v1/stores
  GET    /api/v1/stores/{store_id}
  PUT    /api/v1/stores/{store_id}
  DELETE /api/v1/stores/{store_id}

LAYOUTS
  POST   /api/v1/layouts
  GET    /api/v1/layouts/{layout_id}
  PUT    /api/v1/layouts/{layout_id}
  GET    /api/v1/layouts/{layout_id}/versions
  POST   /api/v1/layouts/{layout_id}/rollback/{version_id}

ZONES
  POST   /api/v1/zones
  PUT    /api/v1/zones/{zone_id}
  DELETE /api/v1/zones/{zone_id}

SHELVES
  POST   /api/v1/shelves
  PUT    /api/v1/shelves/{shelf_id}
  DELETE /api/v1/shelves/{shelf_id}

PRODUCTS
  POST   /api/v1/products
  GET    /api/v1/products
  PUT    /api/v1/products/{product_id}
  DELETE /api/v1/products/{product_id}
  POST   /api/v1/products/import          ← CSV

PLACEMENTS
  POST   /api/v1/placements
  GET    /api/v1/placements?shelf_id=
  PUT    /api/v1/placements/{placement_id}
  DELETE /api/v1/placements/{placement_id}

SALES
  POST   /api/v1/sales
  GET    /api/v1/sales?store_id=
  PUT    /api/v1/sales/{sales_id}
  DELETE /api/v1/sales/{sales_id}
  POST   /api/v1/sales/import             ← CSV

ANALYTICS
  GET    /api/v1/analytics/{layout_id}/overview
  GET    /api/v1/analytics/{layout_id}/shelves
  GET    /api/v1/analytics/{layout_id}/zones
  GET    /api/v1/analytics/{layout_id}/skus
```

---

## 🔁 WHAT COMES AFTER MVP

When MVP is shipped, the next additions slot in without touching existing architecture:

- **Phase 2:** Redis for caching analytics, WebSocket service for collaboration, first AI shelf suggestion using existing placement + sales data, full Three.js 3D planogram rendering (replacing the MVP placeholder)
- **Phase 3:** POS connector replaces CSV upload path; dead zone detection enabled by connected footfall data; Computer Vision service for shelf image matching
- **Phase 4:** Multi-store sync, Kubernetes, MongoDB for layout graph scale

---

**Status:** 🚧 MVP — In Active Planning
**Version:** 1.0
