# 📘 EUREKA – PRODUCT REQUIREMENTS DOCUMENT (PRD) — MVP

---

## 1. 🧠 Product Overview

Eureka is an AI-powered retail store intelligence platform. The **MVP** delivers the foundational design and measurement engine: a canvas-based store layout builder, intelligent product placement, and basic analytics — giving retail teams a fast, intuitive tool to plan and evaluate their store environments.

> **MVP Core Loop:** Design → Product Placement → Basic Analytics

---

## 2. 🎯 MVP Goals & Objectives

- Deliver an intuitive drag-and-drop canvas for full store and shelf design
- Enable size-aware and category-intelligent product placement
- Provide basic analytics to measure layout and SKU performance
- Establish a clean, scalable foundation for future AI and collaboration features

---

## 3. 👥 Target Users (MVP)

| Role | Primary Use |
|------|-------------|
| **Merchandiser** | Design and manage store layouts and shelf planograms |
| **Category Manager** | Place products by category logic, review performance |
| **Store Manager** | View layouts and basic performance reports |

> Auditors, Suppliers, and Retail HQ Teams are **out of scope** for MVP.

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
- Grid snapping is accurate to configured unit (cm/inch)
- Layout saves persist across sessions

**Value:** Fast, intuitive design experience — Canva/Figma-like for retail

---

### 4.2 📦 Product Placement (Size + Category)

**Description:** Place products on shelves with awareness of their physical dimensions and semantic category.

**Capabilities:**
- Product master list with SKU, name, dimensions (width, height, depth), category, brand, and price
- Drag products from the product panel onto shelf slots
- Size-aware placement: products occupy accurate shelf space proportional to their dimensions
- Category grouping: visually group and color-code products by category or brand
- Brand blocking: place multiple facings of the same SKU side by side
- Facing count display and calculation per shelf row

**Acceptance Criteria:**
- Product dimensions correctly translate to shelf space occupation
- Facings are counted and displayed per product per shelf
- Category and brand filters work on the product panel

**Value:** Realistic, accurate shelf layouts that reflect real-world constraints

---

### 4.3 📊 Basic Analytics

**Description:** Performance measurement for layouts, shelves, and individual SKUs.

**Capabilities:**

#### Sales per Shelf / Zone
- Input or import sales data per SKU
- Display aggregated revenue per shelf section and store zone
- Color-coded performance indicators (high / medium / low)

#### SKU Performance
- Sales volume and revenue per SKU
- Ranking of top and bottom performing products in a layout

#### Revenue per Sq Ft
- Calculate and display revenue density per defined store area
- Flag underperforming zones against store average

#### Layout Performance Score
- Composite score based on space utilization and sales distribution
- Displayed as a summary card on the layout dashboard

**Acceptance Criteria:**
- Analytics update when new sales data is provided
- All metrics are displayed on a simple, readable dashboard
- Data can be viewed at store, zone, shelf, and SKU levels

**Value:** Data-driven layout decisions without needing external BI tools

---

## 5. 🔄 MVP End-to-End User Flow

```
1. User registers / logs in
2. Creates a new store (name, dimensions, store type)
3. Opens layout canvas → designs floor plan using drag & drop
4. Adds shelves to zones
5. Opens product panel → drags products onto shelves
6. Reviews shelf facings and category groupings
7. Saves and names the layout
8. Navigates to Analytics view
9. Inputs or imports basic sales data
10. Views performance metrics (sales per shelf, SKU rankings, revenue/sqft)
```

---

## 6. 🚫 Out of Scope for MVP

The following features are explicitly **excluded** from the MVP and planned for later phases:

| Feature | Planned Phase |
|---------|--------------|
| AI-assisted layout suggestions | Phase 2 |
| Smart Shelf Builder (ML optimization) | Phase 2 |
| Real-time analytics dashboard | Phase 2 |
| Multi-user collaboration | Phase 2 |
| Computer vision / image-based shelf recognition | Phase 3 |
| Heatmap visualization (footfall + shelf interaction) | Phase 3 |
| A/B Testing for layouts | Phase 3 |
| Multi-store sync | Phase 4 |
| Auto replenishment alerts | Phase 4 |
| Supplier portal | Phase 4 |
| Simulation mode | Phase 4 |
| POS / ERP integrations | Phase 4 |

---

## 7. 📊 MVP Success Metrics

| Metric | Target |
|--------|--------|
| Layout creation time (new store) | < 5 minutes |
| Product placement accuracy | Dimensions render correctly 100% of time |
| Analytics load time | < 2 seconds for standard layout |
| User task completion rate | > 85% in usability testing |
| System uptime | 99.5% |

---

## 8. 🔐 Non-Functional Requirements (MVP)

- **Authentication:** JWT-based login; session management
- **Authorization:** Role-based access control (Admin, Merchandiser, Viewer)
- **Performance:** Canvas renders layouts with up to 500 product items without lag
- **Data Security:** All data encrypted in transit (TLS); passwords hashed (bcrypt)
- **Responsiveness:** Optimized for desktop browsers (Chrome, Firefox, Edge); tablet support is a stretch goal

---

## 9. 🗺️ Phasing Roadmap

### ✅ Phase 1 — MVP (Current)
- Layout Builder (drag & drop canvas, templates, versioning)
- Product Placement (size-aware, category/brand grouping, facings)
- Basic Analytics (sales per shelf, SKU performance, revenue/sqft, layout score)

### 🔜 Phase 2
- Smart Shelf Builder (AI optimization)
- Real-Time Analytics Dashboard
- Multi-User Collaboration (live editing, RBAC, comments)
- Dead Zone Detection
- Space Utilization metrics

### 🔮 Phase 3
- Image-Based Shelf Recognition (Computer Vision)
- Footfall and Shelf Interaction Heatmaps
- A/B Testing (store + shelf layouts)

### 🚀 Phase 4
- Multi-Store Sync and centralized layout management
- Auto Replenishment Alerts
- Advanced AI / ML optimization
- POS, ERP, Inventory integrations
- Supplier Portal

---

## 10. 🧠 Key Insight

Eureka's MVP is not just a drawing tool. It is the **data foundation** for a retail intelligence system — every layout, shelf, and product placement decision made in Phase 1 becomes training data and context for the AI, analytics, and automation features that follow.

---

**Status:** 🚧 MVP – In Development
