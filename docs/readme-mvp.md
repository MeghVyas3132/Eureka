# 🚀 Eureka – MVP

> **AI-powered Retail Store Intelligence Platform**
> Design. Place. Analyze.

---

## 🧠 Overview

Eureka is a retail intelligence platform that enables businesses to design store layouts, manage product placement, and measure basic performance — all from a single intuitive interface.

The MVP focuses on delivering a **functional closed-loop core**:

```
Design → Product Placement → Basic Analytics
```

This establishes the foundation upon which AI, computer vision, collaboration, and multi-store capabilities will be layered in future phases.

---

## 🎯 MVP Vision

> Build the core design-and-measure engine for physical retail stores — a canvas where retailers can plan layouts, place products, and get actionable performance data.

---

## 🧩 MVP Scope

Eureka MVP operates across **2 core layers**:

### 🏬 1. Store-Level Design (Macro)
- Store zoning (entrance, aisles, checkout, departments)
- Drag-and-drop layout canvas
- Template-based store setup

### 🧃 2. Shelf-Level Design (Micro)
- Shelf builder with product placement
- Size-aware product positioning
- Category grouping and brand blocking

---

## 🔥 MVP Features

### 1. 🎨 Drag & Drop Layout Builder
- Canva/Figma-like canvas interface
- Design store floor plan with zones and shelves
- Auto snap-to-grid and alignment
- Save, load, and manage layout versions

---

### 2. 📦 Product Placement (Size + Category)
- Real-world product dimensions (width, height, depth)
- Category-based product grouping
- Brand blocking support
- Facing count calculations

---

### 3. 📊 Basic Analytics
- Sales per shelf and store section
- Revenue per sq ft
- SKU-level performance tracking
- Layout performance scoring

---

## 🔄 MVP Workflow

```
1. Define store parameters (dimensions, type)
2. Design store layout on canvas (drag & drop)
3. Add shelves and assign zones
4. Place products on shelves (with size + category logic)
5. View basic analytics (sales, SKU performance, space utilization)
```

---

## 🏗️ Tech Stack

### Frontend
- **Next.js** (React framework, SSR + routing)
- **Konva.js** (Canvas engine for layout editor)

### Backend
- **FastAPI** (Python, async REST API)
- **SQLAlchemy** (ORM for database interactions)
- **Alembic** (Database schema migrations)

### Database
- **PostgreSQL** (Primary structured data store)

### Storage
- **AWS S3 / local file storage** (Product images, layout assets)

---

## 🔐 Security (MVP)
- JWT-based authentication
- Role-based access control (Admin, Merchandiser, Viewer)
- Data encryption in transit (HTTPS/TLS)

---

## 📊 MVP Success Metrics
- Layouts successfully created and saved
- Products placed with dimension accuracy
- Sales-per-shelf data rendered correctly
- Page load and canvas interaction performance

---

## 🗺️ Roadmap Beyond MVP

| Phase | Features |
|-------|----------|
| Phase 2 | Smart Shelf Builder (AI), Real-Time Dashboard, Multi-User Collaboration |
| Phase 3 | Vision AI, Heatmaps, A/B Testing |
| Phase 4 | Multi-Store Sync, Auto Replenishment, Advanced AI |

---

## 🧠 Key Differentiation

| Eureka MVP | Traditional Tools |
|------------|------------------|
| Canvas-based layout design | Spreadsheet/static tools |
| Size + category-aware placement | Manual estimation |
| Built-in analytics layer | Separate BI tools |
| API-first, scalable backend | Monolithic legacy apps |

---

## 📌 Status

🚧 **MVP – In Development**

---

## 🤝 Contribution

Coming soon...

---

## 📄 License

TBD
