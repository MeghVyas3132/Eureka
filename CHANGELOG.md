# Changelog

All notable changes are recorded here. For the live shipped status, see [`docs/STATUS.md`](docs/STATUS.md). For the master spec, see [`prompt.md`](prompt.md).

## Unreleased — planogram MVP

### Added
- Layer 7 export engine: JPEG (Pillow) + PowerPoint (python-pptx) renderers, plus `/api/v1/planograms/{id}/export/{jpeg,pptx}` endpoints with confidence-tier styling and a draft watermark for low-confidence planograms.
- Layer 6 visual editor: Konva canvas with drag/drop across shelves, draggable `ProductBlock`, catalogue `ProductPanel`, `FacingControls`, `ConfidenceBadge` with breakdown popover, `DataQualityBanner` with deep-link CTAs, `ExportMenu`, and `RegenerateButton` with overwrite confirmation.
- Zustand `planogramStore` with optimistic `moveProduct`, `updateFacings`, `addProduct`, `removeProduct`, and shelf reflow.
- Data ingestion landing at `/upload` with Stores / Products / Sales tabs, sample CSV download per tab, and `ImportSummaryCard` with potential-duplicate flags.
- Hierarchical dashboard at `/dashboard` (Country → State → City → Locality → Store) with selected-store detail panel and per-store `DataHealthWidget`.
- Per-store landing page at `/stores/{id}` with a "Generate AI Planogram" CTA, product/sales readiness summary, and inline quota error handling.
- Login redirect: new users land on `/upload`, returning users on `/dashboard`, admins on `/super-admin`.
- Backend `GET /api/v1/admin/stats` global metrics endpoint (totals + utilisation %).
- Quota enforcement at `POST /api/v1/planograms/generate` and `/generate-all` returning `403 quota_exceeded`.
- Super-admin metric cards above tabs and per-user "Usage" column with progress bar.

### Changed
- Admin user count now uses planograms instead of layouts (`AdminUserRead.layout_count` → `planogram_count`).
- Root readme rewritten to describe the shipped planogram product, with quickstart, layer-by-layer status, and test commands.

### Notes
- Older PRD/TRD/readme drafts in `docs/` carry a status banner pointing to the current `prompt.md` + `docs/STATUS.md`.
- `next.config.js` externalises `canvas` so Konva's SSR build doesn't pull in node-canvas.
