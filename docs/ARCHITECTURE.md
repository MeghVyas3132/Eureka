# Architecture

A short walkthrough of how the seven layers in [`../prompt.md`](../prompt.md) map to code. For a detailed shipped log read [`STATUS.md`](STATUS.md).

## Layer flow

```
File upload (CSV / XLSX / PDF)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 2 — Ingestion                                │
│   backend/ingestion/                                │
│     • file_detector            (python-magic)       │
│     • parsers/{csv,excel,pdf}  (pandas/openpyxl/    │
│                                  pdfplumber)        │
│     • validators/{product,sales,store}              │
│     • sku_deduplicator         (rapidfuzz)          │
│     • ingestion_service        (orchestrator)       │
└─────────────────────────────────────────────────────┘
    │ rows + ImportSummary
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3 — Normalisation                            │
│   services/data_normalization                       │
│     • product/sales/store row cleanup               │
│     • category inference + dimension defaults       │
└─────────────────────────────────────────────────────┘
    │ DB upsert (Postgres, async SQLAlchemy)
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3.5 — Assortment Filter                      │
│   services/assortment_filter                        │
│     • sales-coverage / top-N / fallback             │
│     • shelf-capacity cap, never returns 0 SKUs      │
└─────────────────────────────────────────────────────┘
    │ included SKUs
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 4 — Store Intelligence                       │
│   services/store_intelligence                       │
│     • abbreviation expansion (RF → Reliance Fresh)  │
│     • PIN inference + parse_confidence              │
│     • build_store_hierarchy()                       │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 5 — Planogram Engine                         │
│   services/planogram_engine                         │
│     • STORE_TYPE_RULES (supermarket/hypermarket/…)  │
│     • rank_skus, calculate_facings,                 │
│       assign_to_shelves                             │
│     • compute_confidence_score (4-dim weighted)     │
│     • build_data_quality_warnings                   │
│     • canonical planogram_json                      │
└─────────────────────────────────────────────────────┘
    │ planogram_json + confidence + warnings
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 6 — Visual Editor (Konva, client-only)       │
│   frontend/components/planogram/                    │
│     PlanogramCanvas, ProductBlock, ProductPanel,    │
│     FacingControls, ConfidenceBadge,                │
│     DataQualityBanner, ExportMenu, RegenerateButton │
│   frontend/store/planogramStore (Zustand)           │
└─────────────────────────────────────────────────────┘
    │ optimistic edits, PUT planogram_json on Save
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 7 — Export                                   │
│   services/export_service                           │
│     • render_planogram_to_jpeg (Pillow)             │
│     • render_planogram_to_pptx (python-pptx)        │
│   GET /api/v1/planograms/{id}/export/{jpeg,pptx}    │
└─────────────────────────────────────────────────────┘
```

## Cross-cutting

- **Auth (Layer 1):** JWT (`python-jose`), bcrypt (`passlib`). All non-auth endpoints require `Authorization: Bearer …` and scope queries by `user_id`.
- **Quota:** Tier defaults in `PlanLimit`, per-user overrides on `User`. Resolved via `services/plan_limit_service.resolve_user_plan_limit`. Enforced on planogram generate via `_enforce_planogram_quota`.
- **Versioning:** Every Save snapshots into `planogram_versions` (last 20 retained). Rollback API exposed.
- **Multi-tenant isolation:** every query joins through `Store.user_id` or filters `User.id = current_user.id`.

## Routing & redirects (frontend)

- `/login` → on success, `resolvePostLoginRoute()` decides:
  - `admin` → `/super-admin`
  - user with stores → `/dashboard`
  - new user with no stores → `/upload`
- `/dashboard` → `HierarchyTree` (Country → State → City → Locality) → click a store → `/stores/{id}`
- `/stores/{id}` → "Generate AI Planogram" CTA → `/stores/{id}/planogram/{pid}`
- `/stores/{id}/planogram/{pid}` → Konva editor + export

See [`STATUS.md` §3](STATUS.md) for the full route inventory.
