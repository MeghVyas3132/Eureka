# ⚙️ EUREKA – TECHNICAL REQUIREMENTS DOCUMENT (TRD) — MVP v2

---

## 1. 🧠 System Overview

Eureka MVP is a **fully standalone** web-based retail layout and analytics platform. It provides a canvas-based store design editor, size-aware product placement, and an analytics layer powered by manually entered or CSV-uploaded data.

**No external data integrations exist in MVP.** Eureka does not connect to any POS, ERP, WMS, or inventory system. All data enters the platform through user-initiated actions (manual entry or file upload).

**MVP Architecture Loop:**

```
Design (Canvas) → Save (API + DB) → Import Data (CSV / Manual) → Analyze → View (Dashboard)
```

---

## 2. 🏗️ High-Level Architecture

### Core Layers (MVP):

1. **Frontend Layer** — Next.js canvas application
2. **API Layer** — FastAPI REST backend
3. **Backend Services Layer** — Layout, Product, Analytics, File Ingestion
4. **Data Layer** — PostgreSQL via SQLAlchemy + Alembic
5. **Storage Layer** — AWS S3 / local (product images, uploaded CSV files)

> **Explicitly excluded from MVP architecture:**
> - Any webhook receivers or outbound integration clients
> - POS / ERP / WMS connector services
> - Real-time data pipeline (Kafka, Redis Streams, etc.)
> - WebSocket collaboration service
> - AI/ML inference service
> - Computer Vision service
> - Multi-store sync service

These are deferred to Phase 2–4 and will be added as discrete microservices without requiring architectural rework of the MVP core.

---

## 3. 🎨 Frontend Architecture

### Tech Stack
- **Framework:** Next.js (React, SSR + client-side routing)
- **Canvas Engine:** Konva.js (2D canvas for layout editor)
- **State Management:** Zustand
- **HTTP Client:** Axios / React Query
- **Styling:** Tailwind CSS

### Key Components

| Component | Responsibility |
|-----------|---------------|
| `LayoutCanvas` | Renders the store floor plan; handles drag-and-drop of zones/shelves |
| `ShelfEditor` | Manages shelf slots; renders product facings |
| `ProductPanel` | Lists products from master data; drag source for placement |
| `ProductImporter` | CSV upload UI with field mapping and validation |
| `SalesDataImporter` | CSV upload UI for sales data; maps SKU → revenue/units |
| `ManualSalesEntry` | Form-based manual entry of sales figures per SKU |
| `AnalyticsDashboard` | Displays performance metrics from imported/entered data |
| `DataFreshnessIndicator` | Shows "last updated" timestamp on all analytics views |
| `TemplateSelector` | Store type template picker at layout creation |
| `AuthModule` | Login, registration, JWT token management |

### Routing (Next.js App Router)

```
/                          → Landing / Login
/dashboard                 → Store list
/store/[id]/layout         → Layout Canvas Editor
/store/[id]/analytics      → Analytics Dashboard
/store/[id]/data           → Sales Data Management (import / manual entry)
/products                  → Product Master Data CRUD + CSV import
/settings                  → User & account settings
```

---

## 4. 🌐 API Layer (FastAPI)

### Responsibilities
- REST API serving all frontend requests
- JWT authentication and authorisation
- Request validation (Pydantic models)
- Business logic delegation to service modules
- File upload handling (CSV parsing and ingestion)
- Error handling and structured responses

### API Structure

```
/api/v1/
  /auth            → Login, register, refresh token
  /stores          → Store CRUD
  /layouts         → Layout CRUD, versioning
  /zones           → Zone management within layouts
  /shelves         → Shelf CRUD within zones
  /products        → Product master data CRUD
  /products/import → CSV bulk import for product master data
  /placements      → Product-to-shelf placement management
  /sales           → Sales data CRUD (manual entry)
  /sales/import    → CSV upload and ingestion for sales data
  /analytics       → Metrics computation and retrieval
```

### No Integration Endpoints in MVP
The following endpoint categories are **explicitly absent** from MVP:
- `/webhooks/*` — no inbound webhook receivers
- `/connectors/*` — no POS/ERP/WMS connector routes
- `/sync/*` — no external system sync routes

### Authentication
- **Scheme:** JWT (Bearer token)
- **Library:** `python-jose` + `passlib[bcrypt]`
- **Token Expiry:** Access: 60 min | Refresh: 7 days

---

## 5. 🧱 Backend Services (MVP)

---

### 5.1 Layout Service

**Responsibilities:**
- Create, read, update, delete store layouts
- Manage zones (named areas: aisle, entrance, checkout, etc.)
- Manage shelves within zones (position, dimensions)
- Layout version history (store last N snapshots as JSON in DB)

**Key Logic:**
- Layout state serialised as JSON graph: `{ store_id, zones: [{ id, name, position, shelves: [...] }] }`
- On each save, a versioned snapshot is written to `layout_versions` table
- Rollback restores from snapshot

---

### 5.2 Product Service

**Responsibilities:**
- Manage product master data (SKU library)
- CRUD for products with full attribute set
- Filter/search by category, brand, name
- **CSV import:** parse uploaded file, validate fields, create/update product records

**Product Attributes:**

| Field | Type | Notes |
|-------|------|-------|
| `sku` | string | Unique identifier |
| `name` | string | Display name |
| `brand` | string | Brand name |
| `category` | string | Category tag |
| `width_cm` | float | Physical width |
| `height_cm` | float | Physical height |
| `depth_cm` | float | Physical depth |
| `price` | decimal | Unit price |
| `image_url` | string | S3 asset URL (optional) |

**CSV Import Spec:**
- Accepted columns: `sku, name, brand, category, width_cm, height_cm, depth_cm, price`
- Unknown columns are ignored
- Required: `sku, name`; all dimension fields optional but recommended
- On conflict (duplicate SKU): update existing record
- Returns: import summary (success count, skipped rows, validation errors)

---

### 5.3 Placement Service

**Responsibilities:**
- Record which product is placed on which shelf, at which position
- Track facing count per placement
- Validate placement against shelf capacity (based on product width vs shelf width)

**Placement Record:**

| Field | Notes |
|-------|-------|
| `shelf_id` | FK to shelves |
| `product_id` | FK to products |
| `position_x` | X offset on shelf |
| `facing_count` | Number of facings |

---

### 5.4 Sales Data Service

**Responsibilities:**
- Accept sales data via two paths: manual entry and CSV upload
- Store normalised sales records per SKU per period
- Provide a "data freshness" record (when data was last updated per store)

**Two Ingestion Paths:**

#### Path A — Manual Entry
User enters figures directly via the `/store/[id]/data` page.

```
POST /api/v1/sales
Body: { store_id, sku, period_start, period_end, units_sold, revenue }
```

#### Path B — CSV Upload
User uploads an export from their own POS/ERP.

```
POST /api/v1/sales/import
Content-Type: multipart/form-data
Body: { store_id, file: <csv>, period_start, period_end }
```

**CSV Import Spec:**
- Accepted columns: `sku, units_sold, revenue`
- `period_start` and `period_end` are provided at upload time (not per-row)
- SKUs that don't match known products are flagged in the import summary (not rejected)
- Returns: import summary with matched / unmatched SKU counts
- **No outbound calls are made during import** — data processing is entirely internal

**Data Freshness:**
- Every analytics view shows a `last_updated` timestamp derived from the most recent sales record for that store
- This makes explicit to the user that data is not live

**Sales Data Model:**

| Field | Notes |
|-------|-------|
| `store_id` | FK to stores |
| `sku` | Product identifier |
| `period_start` | Date (provided at import) |
| `period_end` | Date (provided at import) |
| `units_sold` | Integer |
| `revenue` | Decimal |
| `ingestion_method` | `manual` or `csv_import` |
| `created_at` | Timestamp of upload |

---

### 5.5 Analytics Service

**Responsibilities:**
- Compute all metrics from the `sales_data` and `placements` tables — no external data sources
- Return pre-computed metric objects to the frontend dashboard

**Metrics Computed:**

| Metric | Computation | Data source |
|--------|-------------|-------------|
| Sales per shelf | Sum of revenue for all SKUs placed on a shelf | `sales_data` + `placements` |
| Sales per zone | Sum of revenue for all shelves in a zone | `sales_data` + `placements` + `zones` |
| Revenue per sq ft | Zone revenue ÷ zone area | Above + zone dimensions |
| SKU ranking | Revenue DESC sort across all placed products | `sales_data` + `placements` |
| Layout performance score | Composite: space utilisation × sales distribution | All placement + sales data |
| Data freshness timestamp | MAX(created_at) from `sales_data` WHERE store_id | `sales_data` |

**Explicit non-computations (not in MVP):**
- Stockout probability (requires live inventory levels)
- Time-to-stockout (requires live sales velocity)
- Dead zone detection (requires footfall or live sensor data)
- Demand forecast (requires historical connected data at volume)
- Replenishment triggers (requires live inventory signal)

---

## 6. 📁 File Ingestion Pipeline (CSV)

Both product and sales CSV imports follow the same internal pipeline:

```
1. Frontend uploads file (multipart/form-data)
2. API Layer receives file, streams to S3 (raw archive) + temp buffer
3. File Ingestion Service parses CSV (pandas / csv.DictReader)
4. Row-level validation:
   - Required fields present
   - Numeric fields are valid numbers
   - SKU field not empty
5. Batch upsert to PostgreSQL (SQLAlchemy bulk_insert_mappings)
6. Import summary returned:
   {
     total_rows: int,
     success: int,
     skipped: int,
     errors: [{ row: int, reason: str }]
   }
7. Raw CSV archived in S3 for audit trail
```

**Error handling:**
- Partial imports succeed — valid rows are committed even if some rows fail
- No external calls are made during the pipeline
- File size limit: 10 MB per upload
- Maximum rows per upload: 50,000

---

## 7. 🗄️ Data Layer

### Primary Database: PostgreSQL
### ORM: SQLAlchemy (async, asyncpg driver)
### Migrations: Alembic

### Core Tables (MVP)

```
users
  - id, email, hashed_password, role, created_at

stores
  - id, user_id (FK), name, width_m, height_m, store_type, created_at

layouts
  - id, store_id (FK), name, created_at, updated_at

layout_versions
  - id, layout_id (FK), version_number, snapshot_json, created_at

zones
  - id, layout_id (FK), name, zone_type, x, y, width, height

shelves
  - id, zone_id (FK), x, y, width_cm, height_cm, num_rows

products
  - id, sku, name, brand, category, width_cm, height_cm, depth_cm, price, image_url

placements
  - id, shelf_id (FK), product_id (FK), position_x, facing_count

sales_data
  - id, store_id (FK), sku, period_start, period_end,
    units_sold, revenue, ingestion_method, created_at

csv_import_log
  - id, store_id (FK), import_type (product|sales), filename,
    total_rows, success_count, error_count, imported_at, imported_by (FK users)
```

> **No connector tables in MVP.** Tables for `erp_connections`, `pos_sessions`, `webhook_subscriptions`, or `sync_jobs` are absent. Schema is clean and will receive these as separate Alembic migrations in Phase 3.

---

## 8. ☁️ Storage Layer

- **Service:** AWS S3 (production) / local filesystem (development)
- **Stored Assets:**
  - Product images (optional, user-uploaded)
  - Layout thumbnail previews
  - Archived CSV imports (raw files, for audit trail)
- **Access:** Pre-signed URLs for frontend rendering
- **CDN:** CloudFront (production only)

---

## 9. 🔄 MVP Data Flow

```
1. User designs layout on canvas (Next.js / Konva.js)
2. Layout state sent to Layout Service (POST /api/v1/layouts)
3. Layout persisted to PostgreSQL via SQLAlchemy
4. Products fetched from Product Service and rendered on shelf canvas
   (Products entered manually or via CSV import — no external product DB)
5. Placement saved on drag-drop (POST /api/v1/placements)
6. User uploads sales CSV or enters figures manually
   → File Ingestion Service processes → sales_data table populated
7. Analytics Service computes metrics from sales_data + placements tables
8. Metrics returned to frontend Analytics Dashboard
9. Dashboard shows "Last updated: [timestamp]" to indicate data is not live
```

---

## 10. 📊 Data Models (Detail)

### Layout State JSON (stored in `layout_versions.snapshot_json`)

```json
{
  "layout_id": "uuid",
  "store_id": "uuid",
  "zones": [
    {
      "id": "uuid",
      "name": "Aisle 1",
      "zone_type": "aisle",
      "x": 100, "y": 50,
      "width": 400, "height": 120,
      "shelves": [
        {
          "id": "uuid",
          "x": 0, "y": 0,
          "width_cm": 180,
          "num_rows": 4,
          "placements": [
            {
              "product_id": "uuid",
              "sku": "SKU-001",
              "position_x": 0,
              "facing_count": 3
            }
          ]
        }
      ]
    }
  ]
}
```

### Sales Import Summary Response

```json
{
  "import_id": "uuid",
  "store_id": "uuid",
  "imported_at": "2025-04-23T14:32:00Z",
  "period_start": "2025-03-01",
  "period_end": "2025-03-31",
  "total_rows": 120,
  "success": 115,
  "skipped": 3,
  "unmatched_skus": 2,
  "errors": [
    { "row": 14, "reason": "units_sold is not a number" },
    { "row": 67, "reason": "sku is empty" },
    { "row": 89, "reason": "revenue is negative" }
  ]
}
```

---

## 11. 🔐 Security

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT Bearer tokens (`python-jose`) |
| Password storage | bcrypt hashing (`passlib`) |
| Authorisation | Role-based (Admin, Merchandiser, Viewer) via FastAPI `Depends` |
| Transport security | HTTPS / TLS (production) |
| Input validation | Pydantic schemas on all API request bodies |
| File upload validation | MIME type check, size limit (10 MB), virus scan hook (S3 event) |
| Multi-tenancy | All queries scoped by `user_id` / `store_id` at ORM level |
| No outbound calls | MVP backend makes zero outbound HTTP calls to external systems |

---

## 12. ⚡ Performance Targets (MVP)

| Metric | Target |
|--------|--------|
| API response time (p95) | < 300ms |
| Canvas render (500 products) | < 1 second |
| Analytics computation | < 2 seconds |
| CSV import (10,000 rows) | < 5 seconds |
| DB query time (indexed) | < 100ms |

### Optimisation Approaches
- PostgreSQL indexes on `store_id`, `layout_id`, `sku`, `shelf_id`
- Sales data queries use pre-aggregation on upload (aggregate metrics cached per store/period)
- SQLAlchemy bulk upserts for CSV import (not row-by-row)
- Next.js ISR / SSR for dashboard pages

---

## 13. 🧪 Testing Strategy (MVP)

| Level | Tooling | Coverage |
|-------|---------|----------|
| Unit tests (backend) | `pytest` | Core service logic, CSV parser, analytics computations |
| API integration tests | `httpx` + `pytest` | All `/api/v1/` endpoints including import routes |
| CSV import tests | pytest fixtures | Valid CSVs, malformed CSVs, empty files, oversized files, duplicate SKUs |
| DB migration tests | Alembic + test DB | All migration scripts |
| Frontend component tests | Jest + RTL | Canvas, product panel, importer, analytics cards |
| End-to-end tests | Playwright | Create layout → place products → import CSV → view analytics |

---

## 14. 🚀 Deployment (MVP)

| Concern | Stack |
|---------|-------|
| Cloud | AWS (EC2 or ECS Fargate) |
| Database | AWS RDS (PostgreSQL) |
| Storage | AWS S3 + CloudFront |
| CI/CD | GitHub Actions |
| Containerisation | Docker + Docker Compose (dev), ECS (prod) |
| Environment config | `.env` files + AWS Secrets Manager (prod) |
| Monitoring | AWS CloudWatch (basic) |

---

## 15. 🗂️ Project Structure

```
eureka/
├── frontend/
│   ├── app/
│   ├── components/
│   │   ├── canvas/              # Konva layout editor
│   │   ├── analytics/           # Dashboard charts and cards
│   │   ├── products/            # Product panel, CRUD, CSV importer
│   │   └── sales/               # Sales data entry + CSV importer
│   ├── store/                   # Zustand state
│   └── lib/                     # API client, utilities
│
├── backend/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── layouts.py
│   │       ├── products.py
│   │       ├── products_import.py   # CSV import endpoint
│   │       ├── placements.py
│   │       ├── sales.py             # Manual sales entry
│   │       ├── sales_import.py      # CSV sales upload endpoint
│   │       └── analytics.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── layout_service.py
│   │   ├── product_service.py
│   │   ├── placement_service.py
│   │   ├── sales_service.py
│   │   ├── csv_ingestion_service.py  # Shared CSV parser + validator
│   │   └── analytics_service.py
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   └── alembic/
│       └── versions/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 16. 🔁 Post-MVP Architecture Additions (Planned)

| Phase | Addition | Connector dependency |
|-------|---------|---------------------|
| Phase 2 | Redis (caching), WebSocket (collaboration), AI Optimisation Service | None — internal only |
| Phase 3 | POS connector service, ERP/WMS webhooks, live analytics pipeline | First external integrations |
| Phase 3 | Computer Vision Service (YOLO/Detectron2) | Image upload only |
| Phase 3 | Dead zone detection, replenishment alerts | Requires Phase 3 connectors |
| Phase 4 | Multi-Store Sync, MongoDB (scale), Kubernetes | Requires Phase 3 data layer |

---

## 17. 🧠 Final Technical Insight

Eureka MVP is **deliberately connector-free.** This is not a technical limitation — it is a product decision that eliminates the single biggest source of delay and complexity in enterprise retail software (integration projects). By designing a clean CSV ingestion layer now, the backend is primed to swap manual file uploads for automatic data pushes in Phase 3 with minimal rework.

```
Design (Konva) → API (FastAPI) → ORM (SQLAlchemy) → DB (PostgreSQL)
                                        ↓
                             CSV Ingestion Service
                                        ↓
                             Analytics Service
                                        ↓
                             Dashboard (Next.js)
                             [Last updated: timestamp]
```

---

**Status:** 🚧 MVP – In Development
**Version:** 2.0 — Standalone (no data connectors)
