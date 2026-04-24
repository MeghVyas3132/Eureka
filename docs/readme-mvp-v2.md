# 🚀 Eureka – MVP

> **AI-powered Retail Store Intelligence Platform**
> Design. Place. Analyze.

---

## 🧠 Overview

Eureka is a retail intelligence platform that enables businesses to design store layouts, manage product placement, and measure basic performance — all from a single intuitive interface, with **no dependency on external systems**.

The MVP delivers a **fully standalone closed-loop core:**

```
Design → Product Placement → Manual Data Import → Analytics
```

Eureka MVP does not connect to any POS, ERP, WMS, or inventory system. All data enters the platform through manual entry or CSV upload — a deliberate decision that keeps the product simple, fast to ship, and immediately usable by any retailer regardless of their existing tech stack.

---

## 🎯 MVP Vision

> Build the core design-and-measure engine for physical retail stores — a canvas where retailers can plan layouts, place products, and get actionable performance data — without needing to integrate a single external system.

---

## 🧩 MVP Scope

### 🏬 1. Store-Level Design (Macro)
- Store zoning (entrance, aisles, checkout, departments)
- Drag-and-drop layout canvas
- Template-based store setup

### 🧃 2. Shelf-Level Design (Micro)
- Shelf builder with product placement
- Size-aware product positioning
- Category grouping and brand blocking

### 📊 3. Analytics (Manual Data)
- Powered entirely by CSV upload or manual entry
- No live integrations — all data is user-provided

---

## 🔥 MVP Features

### 1. 🎨 Drag & Drop Layout Builder
- Canva/Figma-like canvas interface
- Design store floor plan with zones and shelves
- Auto snap-to-grid and alignment
- Save, load, and manage layout versions

### 2. 📦 Product Placement (Size + Category)
- Real-world product dimensions (width, height, depth)
- Category-based product grouping
- Brand blocking support
- Facing count calculations
- Bulk product import via CSV

### 3. 📊 Basic Analytics (Import-Driven)
- Upload a sales CSV (exported from your own POS/ERP) — or enter data manually
- Sales per shelf and store zone
- Revenue per sq ft (calculated from layout dimensions + imported data)
- SKU-level performance ranking
- Layout performance score
- "Last updated" timestamp on all views — data is not live

---

## 📥 How Data Gets Into Eureka (MVP)

Eureka MVP has **no live data connectors.** Data enters in two ways:

| Method | How |
|--------|-----|
| **CSV Upload** | Export a sales report from your POS or ERP → upload it to Eureka → analytics update immediately |
| **Manual Entry** | Type sales figures per SKU directly in the analytics panel |

This means: no API keys, no IT involvement, no integration project. Any retailer with a basic sales report can use Eureka on day one.

---

## 🚫 What's NOT in MVP

These features require live data connectors and are explicitly deferred:

| Feature | Why deferred |
|---------|-------------|
| Real-time analytics | Requires live POS data feed |
| Auto replenishment alerts | Requires live inventory levels |
| Stockout prediction | Requires live sales velocity |
| Dead zone detection | Requires footfall / sensor data |
| In-season shelf adjustments | Requires live sales signal |
| POS / ERP / WMS integrations | Phase 3 |

---

## 🔄 MVP Workflow

```
1. Define store parameters (dimensions, type)
2. Design store layout on canvas (drag & drop)
3. Add shelves and assign zones
4. Import product catalogue via CSV (or add manually)
5. Place products on shelves (size + category logic)
6. Upload a sales data CSV (or enter figures manually)
7. View analytics — sales per shelf, SKU rankings, revenue/sqft
```

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js + Konva.js |
| Backend | FastAPI (Python, async) |
| ORM | SQLAlchemy + Alembic |
| Database | PostgreSQL |
| Storage | AWS S3 (product images + CSV archives) |
| Auth | JWT (python-jose + passlib) |

**No message queues, no webhook receivers, no external API clients in MVP.**

---

## 🔐 Security
- JWT-based authentication
- Role-based access control (Admin, Merchandiser, Viewer)
- All data encrypted in transit (HTTPS/TLS)
- Zero outbound calls to external systems from backend

---

## 📊 MVP Success Metrics

| Metric | Target |
|--------|--------|
| Layout creation time (new store) | < 5 minutes |
| Product placement accuracy | Dimensions render correctly 100% of time |
| CSV import success rate | > 95% on well-formed files |
| Analytics load time | < 2 seconds after data upload |
| User task completion rate | > 85% in usability testing |
| System uptime | 99.5% |

---

## 🗺️ Roadmap

| Phase | Features |
|-------|----------|
| **Phase 1 (MVP)** | Layout builder, product placement, CSV-driven analytics |
| Phase 2 | Smart Shelf Builder (AI), collaboration, space utilisation, first auto-sync connectors |
| Phase 3 | Live POS/ERP connectors, dead zone detection, replenishment alerts, computer vision |
| Phase 4 | Multi-store sync, advanced AI, IoT integrations, supplier portal |

---

## 📌 Status

🚧 **MVP – In Development**
**v2.0 — Standalone (no data connectors)**
