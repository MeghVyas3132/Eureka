# 📘 EUREKA – PRODUCT REQUIREMENTS DOCUMENT (PRD) — MVP v2

---

## 1. 🧠 Product Overview

Eureka is an AI-powered retail store intelligence platform. The **MVP** delivers the foundational design and measurement engine: a canvas-based store layout builder, intelligent product placement, and manual-data analytics — giving retail teams a fast, intuitive tool to plan and evaluate their store environments.

> **MVP Core Loop:** Design → Product Placement → Manual Data Import → Basic Analytics

### MVP Data Philosophy

Eureka MVP is **fully standalone** — it does not connect to any external systems (POS, ERP, WMS, inventory, or accounting software) in this phase. All data enters Eureka through:
- **Manual entry** directly in the app
- **CSV / spreadsheet upload** for bulk data

This is a deliberate scoping decision. Integration-dependent features (real-time analytics, auto replenishment, live inventory sync) are explicitly deferred to Phase 2 and beyond.

---

## 2. 🎯 MVP Goals & Objectives

- Deliver an intuitive drag-and-drop canvas for full store and shelf design
- Enable size-aware and category-intelligent product placement
- Provide analytics driven entirely by manually imported or entered data
- Establish a clean, scalable foundation for future AI, connector, and collaboration features

---

## 3. 👥 Target Users (MVP)

| Role | Primary Use |
|------|-------------|
| **Visual Merchandiser / Planogram Manager** | Design store layouts and shelf planograms; manage SKU placement |
| **Category Manager** | Place products by category logic, input sales data, review performance |
| **Store Manager** | View layouts and basic performance summaries |

> Auditors, Suppliers, Retail HQ Teams, and roles requiring live data feeds are **out of scope** for MVP.

---

## 4. 🧩 MVP Feature Requirements

---

### 4.1 🎨 Drag & Drop Layout Builder

**Description:** A visual, canvas-based interface to design a store's floor plan and shelf structure.

**Capabilities:**
- Drag and drop zones (entrance, aisles, checkout, department areas) onto the store canvas
- Add, resize, and position shelves within zones
- Auto snap-to-grid and smart alignment guides
- Select from pre-built store templates (supermarket, convenience, specialty)
- Save, rename, duplicate, and delete layouts
- Version history with basic rollback (last N versions)

**Acceptance Criteria:**
- Users can create a store layout from scratch or from a template in under 5 minutes
- Grid snapping is accurate to the configured unit (cm/inch)
- Layout saves persist across sessions

---

### 4.2 📦 Product Placement (Size + Category)

**Description:** Place products on shelves with awareness of their physical dimensions and semantic category.

**Capabilities:**
- Product master list with SKU, name, dimensions (width, height, depth), category, brand, and price
- Drag products from the product panel onto shelf slots
- Size-aware placement: products occupy accurate shelf space proportional to their dimensions
- Category grouping: visually group and colour-code products by category or brand
- Brand blocking: place multiple facings of the same SKU side by side
- Facing count display and calculation per shelf row
- Bulk product import via CSV (SKU, name, dimensions, category, brand, price)

**Acceptance Criteria:**
- Product dimensions correctly translate to shelf space occupation
- Facings are counted and displayed per product per shelf
- Category and brand filters work on the product panel
- CSV import successfully creates products with all required fields

---

### 4.3 📊 Basic Analytics (Manual Data Input)

**Description:** Performance measurement for layouts, shelves, and individual SKUs — powered entirely by manually entered or CSV-uploaded sales data. No live data connectors are used in MVP.

> ⚠️ **Important:** All metrics in this section are derived from data the user provides manually. Eureka does not pull data from any POS, ERP, WMS, or inventory system in MVP. Analytics are as current as the data the user uploads.

#### 4.3.1 Sales Data Entry

**Two methods of getting data into Eureka:**

| Method | Description |
|--------|-------------|
| **Manual entry** | User types in sales figures per SKU directly in the analytics panel |
| **CSV upload** | User exports a sales report from their POS/ERP and uploads it to Eureka. Eureka maps SKU → sales data. |

**CSV format supported:**
```
sku, period_start, period_end, units_sold, revenue
SKU-001, 2025-01-01, 2025-01-31, 240, 48000
```

#### 4.3.2 Sales per Shelf / Zone

- Display aggregated revenue per shelf section and store zone based on uploaded data
- Colour-coded performance indicators (high / medium / low) relative to store average
- Data is static until the user uploads a new file or edits entries

#### 4.3.3 SKU Performance

- Sales volume and revenue per SKU (from uploaded data)
- Ranking of top and bottom performing products in the layout
- Filter by category, zone, or shelf

#### 4.3.4 Revenue per Sq Ft

- Calculate and display revenue density per defined store area
- Flag underperforming zones against store average
- Calculated from: uploaded revenue ÷ zone/shelf area defined in the canvas

#### 4.3.5 Layout Performance Score

- Composite score based on space utilisation and sales distribution
- Displayed as a summary card on the layout dashboard
- Recalculates on new data upload

**What is explicitly NOT in MVP analytics:**
- Real-time or live data feeds
- Automatic data sync from any external system
- Stockout detection or inventory-level visibility
- Replenishment recommendations
- Dead zone detection (requires footfall or live sensor data)
- Demand forecasting

**Acceptance Criteria:**
- Analytics update when new sales data is uploaded or manually entered
- All metrics display on a simple, readable dashboard
- Data is viewable at store, zone, shelf, and SKU levels
- A "last updated" timestamp is shown on all analytics views to make clear the data is not live

---

## 5. 🔄 MVP End-to-End User Flow

```
1.  User registers / logs in
2.  Creates a new store (name, dimensions, store type)
3.  Opens layout canvas → designs floor plan using drag & drop
4.  Adds shelves to zones
5.  Opens product panel → imports products via CSV or adds manually
6.  Drags products onto shelves
7.  Reviews shelf facings and category groupings
8.  Saves and names the layout
9.  Navigates to Analytics view
10. Uploads a sales data CSV (exported from their own POS/ERP)
    OR manually enters sales figures per SKU
11. Views performance metrics (sales per shelf, SKU rankings, revenue/sqft)
12. Iterates on layout based on insights
```

**Step 10 is the key integration point in MVP:** The user bridges the gap between their external systems and Eureka manually. This is intentional — it keeps MVP scope tight while delivering real analytical value.

---

## 6. 🚫 Out of Scope for MVP

The following features are explicitly **excluded** from the MVP:

| Feature | Reason for Exclusion | Planned Phase |
|---------|---------------------|--------------|
| POS / ERP / WMS data connectors | Requires external integrations; out of scope for MVP | Phase 3 |
| Real-time analytics dashboard | Requires live data feed from connected systems | Phase 2 |
| Auto replenishment alerts | Requires live inventory and sales velocity data | Phase 3 |
| Stockout prediction | Requires live or near-live POS data | Phase 3 |
| Dead zone detection | Requires footfall sensors or live in-store data | Phase 3 |
| Demand forecasting | Requires historical connected data at volume | Phase 3 |
| In-season shelf adjustments (AI-triggered) | Requires live sales signal; no connector in MVP | Phase 3 |
| AI-assisted layout suggestions | Deferred post-MVP | Phase 2 |
| Smart Shelf Builder (ML optimisation) | Deferred post-MVP | Phase 2 |
| Multi-user collaboration | Deferred post-MVP | Phase 2 |
| Computer vision / shelf recognition | Deferred | Phase 3 |
| Heatmap visualisation | Requires sensor data | Phase 3 |
| A/B Testing for layouts | Deferred | Phase 3 |
| Multi-store sync | Deferred | Phase 4 |
| Supplier portal | Deferred | Phase 4 |
| Simulation mode | Deferred | Phase 4 |

---

## 7. 📊 MVP Success Metrics

| Metric | Target |
|--------|--------|
| Layout creation time (new store) | < 5 minutes |
| Product placement accuracy | Dimensions render correctly 100% of time |
| CSV upload success rate | > 95% on well-formed files |
| Analytics load time (after data upload) | < 2 seconds |
| User task completion rate | > 85% in usability testing |
| System uptime | 99.5% |

---

## 8. 🔐 Non-Functional Requirements (MVP)

- **Authentication:** JWT-based login; session management
- **Authorisation:** Role-based access control (Admin, Merchandiser, Viewer)
- **Performance:** Canvas renders layouts with up to 500 product items without lag
- **Data Security:** All data encrypted in transit (TLS); passwords hashed (bcrypt)
- **Data Isolation:** No external system can push or pull data from Eureka in MVP — all I/O is user-initiated
- **Responsiveness:** Optimised for desktop browsers (Chrome, Firefox, Edge); tablet support is a stretch goal

---

## 9. 🗺️ Phasing Roadmap (Updated)

### ✅ Phase 1 — MVP (Current)
- Layout Builder (drag & drop canvas, templates, versioning)
- Product Placement (size-aware, category/brand grouping, facings)
- Product CSV import
- Basic Analytics powered by **manual entry + CSV upload only**
  - Sales per shelf/zone
  - SKU performance ranking
  - Revenue per sq ft
  - Layout performance score

### 🔜 Phase 2
- Smart Shelf Builder (AI optimisation)
- Real-Time Analytics Dashboard (first connector: POS CSV auto-sync / webhook)
- Multi-User Collaboration (live editing, RBAC, comments)
- Space Utilisation metrics
- AI-assisted layout suggestions

### 🔮 Phase 3
- POS / ERP / WMS live data connectors
- Dead Zone Detection (using connected sales + footfall data)
- Auto Replenishment Alerts (connected inventory + sales velocity)
- Stockout prediction and in-season shelf adjustment triggers
- Image-Based Shelf Recognition (Computer Vision)
- Footfall and Shelf Interaction Heatmaps
- A/B Testing (store + shelf layouts)

### 🚀 Phase 4
- Multi-Store Sync and centralised layout management
- Advanced AI / ML optimisation with full data loop
- Supplier Portal
- IoT sensor integrations

---

## 10. 🧠 Key Insight

Eureka's MVP intentionally sidesteps the integration complexity that kills most retail software projects. By asking users to bring their own data (via CSV), the product can deliver **real analytical value on day one** without a single API integration.

The trade-off is accepted: users have one manual step (export from POS → upload to Eureka). This is a friction that disappears in Phase 3 when connectors are built — and by then, users will already be dependent on the platform for their layouts, placements, and planning decisions.

> Every layout, shelf, and product placement decision made in Phase 1 becomes the training data and context for the AI, live analytics, and automation features in Phase 2 and beyond.

---

**Status:** 🚧 MVP – In Development
**Version:** 2.0 — Standalone (no data connectors)
