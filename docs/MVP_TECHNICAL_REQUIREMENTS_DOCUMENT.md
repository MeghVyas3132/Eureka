# ⚙️ EUREKA – TECHNICAL REQUIREMENTS DOCUMENT (TRD) — MVP

> ⚠️ **Status note (updated 2026-05-08):** This is an **archived TRD iteration**. The current shipped MVP follows [`prompt.md`](../prompt.md) (planogram platform). For what's actually built and deployed, see [`docs/STATUS.md`](STATUS.md) and the root [`readme.md`](../readme.md). Prefer `MVP_TECHNICAL_REQUIREMENTS_DOCUMENT_v2.md` over this file for the historical v2 record.

---

## 1. 🧠 System Overview

Eureka MVP is a web-based retail layout and analytics platform. It provides a canvas-based store design editor, size-aware product placement, and a basic analytics layer — all backed by a clean, scalable API-first architecture.

**MVP Architecture Loop:**

```
Design (Canvas) → Save (API + DB) → Analyze (Analytics Service) → View (Dashboard)
```

---

## 2. 🏗️ High-Level Architecture

### Core Layers (MVP):

1. **Frontend Layer** — React.js 18 (Vite SPA) canvas application
2. **API Layer** — FastAPI REST backend
3. **Backend Services Layer** — Layout, Product, Analytics
4. **Data Layer** — PostgreSQL via SQLAlchemy + Alembic
5. **Storage Layer** — AWS S3 / local (product images, assets)

> AI/ML Layer, Computer Vision Service, Collaboration Service, and Multi-Store Sync are **deferred to post-MVP phases**.

---

## 3. 🎨 Frontend Architecture

### Tech Stack
- **Framework:** React.js 18 (Vite, SPA — client-side only, no SSR)
- **Routing:** React Router v6 (`react-router-dom`)
- **Canvas Engine (2D):** Konva.js (layout editor, planogram editor, shelf builder)
- **Canvas Engine (3D):** Three.js (future 3D planogram view — installed now, used in Phase 2)
- **State Management:** Zustand
- **HTTP Client:** Axios / TanStack React Query
- **Styling:** Tailwind CSS

### Key Components

| Component | Responsibility |
|-----------|---------------|
| `LayoutCanvas` | Renders the store floor plan; handles drag-and-drop of zones/shelves |
| `ShelfEditor` | Manages shelf slots; renders product facings |
| `ProductPanel` | Lists products from master data; drag source for placement |
| `AnalyticsDashboard` | Displays sales/performance metrics in charts and cards |
| `TemplateSelector` | Store type template picker at layout creation |
| `AuthModule` | Login, registration, JWT token management |

### Routing (React Router v6)

Defined in `src/App.tsx` using `<BrowserRouter>` and `<Routes>`.
Auth guard: `src/router/ProtectedRoute.tsx` wraps all authenticated routes.

```
/                        → Landing / Login
/dashboard               → Store list
/store/:id/layout        → Layout Canvas Editor
/store/:id/analytics     → Analytics Dashboard
/store/:id/data          → Sales Data Management
/products                → Product Master Data CRUD
/settings                → User & account settings
```

---

## 4. 🌐 API Layer (FastAPI)

### Responsibilities
- REST API serving all frontend requests
- JWT authentication and authorization
- Request validation (Pydantic models)
- Business logic delegation to service modules
- Error handling and structured responses

### API Structure

```
/api/v1/
  /auth          → Login, register, refresh token
  /stores        → Store CRUD
  /layouts       → Layout CRUD, versioning
  /zones         → Zone management within layouts
  /shelves       → Shelf CRUD within zones
  /products      → Product master data CRUD
  /placements    → Product-to-shelf placement management
  /analytics     → Sales data input + metrics retrieval
```

### Authentication
- **Scheme:** JWT (Bearer token)
- **Library:** `python-jose` + `passlib[bcrypt]`
- **Token Expiry:** Access token: 60 min | Refresh token: 7 days

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
- Layout state serialized as JSON graph: `{ store_id, zones: [{ id, name, position, shelves: [...] }] }`
- On each save, a versioned snapshot is written to `layout_versions` table
- Rollback restores from snapshot

---

### 5.2 Product Service

**Responsibilities:**
- Manage product master data (SKU library)
- CRUD for products with full attribute set
- Filter/search by category, brand, name

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
| `image_url` | string | S3 asset URL |

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

### 5.4 Analytics Service

**Responsibilities:**
- Accept sales data input (manual entry or CSV upload per SKU)
- Compute metrics:
  - **Sales per Shelf Section** — aggregate sales of all products on a shelf
  - **Revenue per Sq Ft** — shelf/zone revenue ÷ area
  - **SKU Performance** — rank products by revenue and volume
  - **Layout Performance Score** — composite metric (space utilization × sales distribution)
- Return pre-computed metric objects to frontend

**Sales Data Model:**

| Field | Notes |
|-------|-------|
| `store_id` | FK to stores |
| `sku` | Product identifier |
| `period_start` | Date |
| `period_end` | Date |
| `units_sold` | Integer |
| `revenue` | Decimal |

---

## 6. 🗄️ Data Layer

### Primary Database: PostgreSQL

All structured data is stored in PostgreSQL.

### ORM: SQLAlchemy

- All DB interactions go through SQLAlchemy ORM models
- Async SQLAlchemy (`asyncpg` driver) for non-blocking I/O with FastAPI

### Migrations: Alembic

- All schema changes managed via Alembic migration scripts
- Migration files versioned in `alembic/versions/`
- Command: `alembic upgrade head` applied on deployment

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
  - id, store_id (FK), sku, period_start, period_end, units_sold, revenue
```

---

## 7. ☁️ Storage Layer

- **Service:** AWS S3 (production) / local filesystem (development)
- **Stored Assets:** Product images, layout thumbnail previews
- **Access:** Pre-signed URLs for frontend image rendering
- **CDN:** CloudFront (production only) for fast asset delivery

---

## 8. 🔄 MVP Data Flow

```
1. User designs layout on canvas (React.js + Vite / Konva.js 2D)
2. Layout state sent to Layout Service (POST /api/v1/layouts)
3. Layout persisted to PostgreSQL via SQLAlchemy
4. Products fetched from Product Service and rendered on shelf canvas
5. Placement saved on drag-drop (POST /api/v1/placements)
6. Sales data entered/uploaded via Analytics Service
7. Analytics Service computes metrics from sales_data + placements tables
8. Metrics returned to frontend Analytics Dashboard
```

---

## 9. 📊 Data Models (Detail)

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

---

## 10. 🔐 Security

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT Bearer tokens (`python-jose`) |
| Password storage | bcrypt hashing (`passlib`) |
| Authorization | Role-based (Admin, Merchandiser, Viewer) enforced via FastAPI `Depends` |
| Transport security | HTTPS / TLS (enforced in production) |
| Input validation | Pydantic schemas on all API request bodies |
| Multi-tenancy | All queries scoped by `user_id` / `store_id` at ORM level |

---

## 11. ⚡ Performance Targets (MVP)

| Metric | Target |
|--------|--------|
| API response time (p95) | < 300ms |
| Canvas render (500 products) | < 1 second |
| Analytics computation | < 2 seconds |
| DB query time (indexed) | < 100ms |

### Optimization Approaches
- PostgreSQL indexes on `store_id`, `layout_id`, `sku`, `shelf_id`
- SQLAlchemy lazy loading minimized; explicit joins used for analytics queries
- Vite code splitting (`React.lazy` + `Suspense`) for dashboard pages
- TanStack React Query caching to minimise re-fetches

---

## 12. 🧪 Testing Strategy (MVP)

| Level | Tooling | Coverage Target |
|-------|---------|----------------|
| Unit tests (backend) | `pytest` | Core service logic |
| API integration tests | `httpx` + `pytest` | All `/api/v1/` endpoints |
| DB migration tests | Alembic + test DB | All migration scripts |
| Frontend component tests | Vitest + React Testing Library | Key canvas + form components |
| End-to-end tests | Playwright | Core user flows (create layout, place product, view analytics) |

---

## 13. 🚀 Deployment (MVP)

| Concern | Stack |
|---------|-------|
| Cloud | AWS (EC2 or ECS Fargate) |
| Database | AWS RDS (PostgreSQL) |
| Storage | AWS S3 + CloudFront |
| CI/CD | GitHub Actions |
| Containerization | Docker + Docker Compose (dev), ECS (prod) |
| Environment config | `.env` files + AWS Secrets Manager (prod) |
| Monitoring | AWS CloudWatch (basic) |

### CI/CD Pipeline

```
Push to main →
  1. Run tests (pytest + vitest)
  2. Build Docker images
  3. Run Alembic migrations (alembic upgrade head)
  4. Deploy to ECS / EC2
```

---

## 14. 🗂️ Project Structure

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
│   │   │   └── ProtectedRoute.tsx     # Auth guard
│   │   ├── store/                     # Zustand state slices
│   │   └── lib/                       # Axios instance, utils
│
├── backend/                     # FastAPI app
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── layouts.py
│   │       ├── products.py
│   │       ├── placements.py
│   │       └── analytics.py
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Business logic (layout, product, analytics)
│   ├── db/
│   │   ├── session.py           # Async DB session setup
│   │   └── base.py              # Declarative base
│   └── alembic/
│       ├── env.py
│       └── versions/            # Migration scripts
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 15. 🔁 Post-MVP Architecture Additions (Planned)

| Phase | Addition |
|-------|---------|
| Phase 2 | Redis (real-time collab + caching), WebSocket service, AI Optimization Service, Three.js 3D planogram view |
| Phase 3 | Computer Vision Service (YOLO/Detectron2), Heatmap Engine |
| Phase 4 | Multi-Store Sync Service, MongoDB (flexible layout graphs at scale), Kubernetes |

---

## 16. 🧠 Final Technical Insight

Eureka MVP is deliberately **simple in scope, but production-quality in foundation**. The FastAPI + SQLAlchemy + Alembic + PostgreSQL stack gives the project clean async performance, strict schema control, and zero-friction migration management — ensuring that every Phase 2–4 feature can be bolted on without architectural rework.

```
Design (Konva 2D / Three.js 3D) → API (FastAPI) → ORM (SQLAlchemy) → DB (PostgreSQL)
                                  ↓
                         Analytics Service
                                  ↓
                         Dashboard (React.js + Vite SPA)
```

---

**Status:** 🚧 MVP – In Development
