# Testing

## Backend

```bash
# Service-level unit tests (no Postgres required)
make test-services
# or:
docker compose exec backend poetry run pytest tests/services/ -v

# Full suite (requires Postgres reachable on the test DSN)
make test
# or:
docker compose exec backend poetry run pytest -v
```

Coverage areas:

| File | Layer covered |
|------|----------------|
| `backend/tests/services/test_export_service.py` | JPEG + PPTX rendering, draft watermark, all confidence tiers |
| `backend/tests/services/test_assortment_filter.py` | Sales-coverage / top-N / fallback paths |
| `backend/tests/services/test_store_intelligence.py` | Abbreviation expansion, PIN inference, parse confidence |
| `backend/tests/ingestion/test_sku_deduplicator.py` | Fuzzy matching threshold, intra-file vs cross-import |
| `backend/tests/ingestion/test_ingestion_service.py` | Pipeline orchestration |
| `backend/tests/test_planogram_generate.py` | End-to-end planogram generation |
| `backend/tests/test_products_api.py` | Product CRUD + import |
| `backend/tests/test_sales_api.py` | Sales CRUD + import |
| `backend/tests/test_admin_users.py` | Admin user listing + planogram count + plan limit override |
| `backend/tests/test_stores.py` | Store CRUD + import |

## Frontend

```bash
make typecheck     # tsc --noEmit
make build         # Next.js production build (catches Konva SSR issues)
```

Optional unit tests live under `frontend/__tests__/` (Jest + Testing Library). Konva components are client-only (`next/dynamic({ ssr: false })`) and not exercised by Jest in the current setup.

## Manual UI test plan

See [`STATUS.md` §10](STATUS.md) and the root [`../readme.md`](../readme.md). Short version:

1. Register, log in → land on `/upload`
2. Upload sample CSVs from [`samples/`](samples/) (stores → products → sales)
3. Dashboard → click a store → "Generate AI Planogram"
4. Drag SKUs across shelves, hit `+` on facings, Save
5. Export ▼ → JPEG / PPTX
6. As admin: confirm `/super-admin` shows global stats + per-user usage
