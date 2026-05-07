# 🤖 EUREKA — MASTER CODEX PROMPT v2
## Retail Planogram Platform · Upload → Structure → Generate → Edit → Export

---

## 0. HOW TO READ THIS PROMPT

This is the single authoritative implementation spec for Eureka Pilot. It is complete and self-contained — no other document is needed.

Each section is structured as:
- **WHAT** — what to build
- **HOW** — exactly how to implement it
- **RULES** — hard constraints that cannot be violated
- **NOT** — what to explicitly skip

Read every section before writing any code. When in doubt, refer to the **Final Rule** at the end.

---

## 1. PRODUCT IDENTITY

**Eureka is a self-serve retail planogram platform.**

It is not a data warehouse. It is not an ERP. It is not an analytics tool.

It is a system that does exactly one thing:

```
Messy retail data (CSV / Excel / PDF)
         ↓
  Normalised product + sales + store data
         ↓
  Filtered assortment per store
         ↓
  Auto-generated planograms with confidence scoring
         ↓
  User edits in visual editor
         ↓
  Export as JPEG / PPTX
```

**Primary success metric:**
> User uploads a file → sees a usable planogram → within 2 minutes.

Every engineering decision must be evaluated against this metric.

---

## 2. TECH STACK (STRICT — DO NOT DEVIATE)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | **Next.js 14** (App Router, TypeScript) | |
| Canvas / Editor | **Konva.js** + `react-konva` | Planogram visual editor |
| Frontend state | **Zustand** | |
| HTTP client | **Axios** + **TanStack React Query** | |
| Styling | **Tailwind CSS** | |
| Backend | **FastAPI** (Python, async) | |
| ORM | **SQLAlchemy** (async, `asyncpg` driver) | |
| Migrations | **Alembic** | |
| Database | **PostgreSQL** | |
| Auth | **JWT** — `python-jose` + `passlib[bcrypt]` | |
| File parsing | `pandas`, `openpyxl`, `pdfplumber`, `chardet`, `python-magic` | |
| SKU deduplication | `rapidfuzz==3.9.7` | Fuzzy name matching |
| Image export | `Pillow` (PIL) | JPEG planogram export |
| PPTX export | `python-pptx` | Presentation export |
| Storage | **AWS S3** / local filesystem (dev) | Uploaded files + exports |
| Containerisation | Docker + docker-compose | |

**No message queues. No Celery. No Redis. No ML models. No external API clients.
All processing is synchronous. All data entry is user-initiated.**

---

## 3. DATABASE SCHEMA

All tables use UUID primary keys. All queries are scoped by `user_id` (multi-tenant isolation).

### 3.1 Core Tables

```sql
-- Users
users:
  id UUID PK, email TEXT UNIQUE, hashed_password TEXT,
  role TEXT DEFAULT 'merchandiser',   -- admin | merchandiser | viewer
  created_at TIMESTAMP

-- Stores (user's store portfolio)
stores:
  id UUID PK, user_id UUID FK(users),
  raw_name TEXT NOT NULL,             -- original name as uploaded: "Reliance Fresh Indiranagar Bangalore"
  display_name TEXT,                  -- cleaned display name
  country TEXT DEFAULT 'India',
  state TEXT,                         -- e.g. "Karnataka"
  city TEXT,                          -- e.g. "Bangalore"
  locality TEXT,                      -- e.g. "Indiranagar"
  store_type TEXT,                    -- supermarket | convenience | hypermarket | specialty | wholesale | unknown
  detected_chain TEXT,                -- e.g. "Reliance Fresh" (expanded from abbreviation)
  pin_code TEXT,                      -- 6-digit Indian PIN code if detected
  parse_confidence FLOAT DEFAULT 0.0, -- 0.0–1.0 from StoreIntelligenceEngine
  source TEXT,                        -- 'manual' | 'file_import'
  created_at TIMESTAMP

-- Products (user's product catalogue — scoped to user, not store)
products:
  id UUID PK, user_id UUID FK(users),
  sku TEXT NOT NULL,                  -- UNIQUE per user
  name TEXT NOT NULL,
  brand TEXT, category TEXT,
  width_cm FLOAT, height_cm FLOAT, depth_cm FLOAT,
  price DECIMAL,
  image_url TEXT,
  created_at TIMESTAMP
  -- CONSTRAINT: UNIQUE(user_id, sku)

-- Sales data (per SKU per store per period)
sales_data:
  id UUID PK, store_id UUID FK(stores),
  sku TEXT NOT NULL,
  period_start DATE, period_end DATE,
  units_sold INT, revenue DECIMAL,
  ingestion_method TEXT,              -- 'manual' | 'file_import'
  created_at TIMESTAMP
  -- CONSTRAINT: UNIQUE(store_id, sku, period_start, period_end) → upsert on conflict

-- Planograms
planograms:
  id UUID PK, store_id UUID FK(stores),
  name TEXT DEFAULT 'Auto-Generated Planogram',
  generation_level TEXT,              -- 'store' | 'city' | 'state'
  generation_method TEXT,             -- 'auto' | 'manual'
  shelf_count INT DEFAULT 5,
  shelf_width_cm FLOAT DEFAULT 180.0,
  shelf_height_cm FLOAT DEFAULT 200.0,
  planogram_json JSONB NOT NULL,      -- canonical planogram state (see Section 9.7)
  is_user_edited BOOLEAN DEFAULT FALSE,
  last_auto_generated_at TIMESTAMP,
  created_at TIMESTAMP, updated_at TIMESTAMP

-- Planogram versions (rollback support — keep last 20 per planogram)
planogram_versions:
  id UUID PK, planogram_id UUID FK(planograms),
  version_number INT, snapshot_json JSONB, created_at TIMESTAMP

-- Unified import audit log (all file uploads)
import_log:
  id UUID PK,
  user_id UUID FK(users),
  store_id UUID FK(stores) NULLABLE,  -- NULL for product imports (user-scoped)
  import_type TEXT,                   -- 'product' | 'sales' | 'store'
  file_format TEXT,                   -- 'csv' | 'excel' | 'pdf'
  original_filename TEXT, file_size_bytes INT, s3_key TEXT,
  total_rows INT, success_count INT, skipped_count INT, error_count INT,
  error_detail JSONB,                 -- [{row, reason}] capped at 100 entries
  status TEXT,                        -- 'completed' | 'partial' | 'failed'
  period_start TEXT, period_end TEXT, -- sales imports only
  unmatched_skus JSONB,               -- sales imports: SKUs not in product catalogue
  imported_at TIMESTAMP
```

### 3.2 Required PostgreSQL Indexes

```sql
CREATE INDEX idx_products_user_sku    ON products(user_id, sku);
CREATE INDEX idx_sales_store_sku      ON sales_data(store_id, sku);
CREATE INDEX idx_sales_period         ON sales_data(store_id, period_start, period_end);
CREATE INDEX idx_planograms_store     ON planograms(store_id);
CREATE INDEX idx_stores_user          ON stores(user_id);
CREATE INDEX idx_stores_hierarchy     ON stores(user_id, country, state, city);
CREATE INDEX idx_import_log_user      ON import_log(user_id);
CREATE INDEX idx_import_log_store     ON import_log(store_id);
```

---

## 4. SYSTEM LAYERS (BUILD IN THIS ORDER)

```
Layer 1:   Auth
Layer 2:   File Ingestion (CSV / Excel / PDF) + SKU Deduplication
Layer 3:   Data Normalisation
Layer 3.5: Assortment Filter
Layer 4:   Store Intelligence Engine
Layer 5:   Planogram Engine (store-type rules + confidence scoring + data quality warnings)
Layer 6:   Visual Editor (Konva) + Confidence UX + Data Quality Banners
Layer 7:   Export Engine (JPEG + PPTX)
```

Do not build a later layer before an earlier one is fully tested.

---

## 5. LAYER 1 — AUTH

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login` → returns `{ access_token, refresh_token }`
- `POST /api/v1/auth/refresh`
- All other endpoints require `Authorization: Bearer <token>`
- Roles: `admin`, `merchandiser`, `viewer`
- Passwords: bcrypt via `passlib`
- Access token TTL: 60 min. Refresh token TTL: 7 days.

---

## 6. LAYER 2 — FILE INGESTION + SKU DEDUPLICATION

### 6.1 What it accepts

| Entity | Formats accepted |
|--------|-----------------|
| Product data | CSV, Excel (.xlsx / .xls), PDF |
| Sales data | CSV, Excel (.xlsx / .xls), PDF |
| Store list | CSV, Excel (.xlsx / .xls) |

### 6.2 Ingestion Pipeline

```
UploadFile (multipart/form-data)
    ↓
[1] File Detection     — detect format from file BYTES via python-magic, NOT Content-Type header
    ↓
[2] Size Check         — reject > 10 MB (HTTP 413), reject 0 bytes (HTTP 400)
    ↓
[3] Parser             — CSVParser | ExcelParser | PDFParser → List[Dict]
    ↓
[4] Column Normaliser  — lowercase all keys, strip whitespace, replace spaces with underscores
    ↓
[5] Validator          — row-level validation; collect errors; NEVER abort entire file on bad rows
    ↓
[6] SKU Deduplicator   — fuzzy match incoming product names against DB + other rows in file
    ↓                    (informational only — does NOT block import)
[7] Upsert             — SQLAlchemy bulk upsert to target table (conflict = UPDATE)
    ↓
[8] Archive            — store raw file to S3 / local for audit trail
    ↓
[9] Import Log         — write ImportLog record
    ↓
[10] Response          — ImportSummaryResponse with counts + errors + duplicate flags
```

### 6.3 Parser Implementations

**CSVParser:**
- Detect encoding via `chardet` (handles UTF-8, UTF-8-BOM, Latin-1, Windows-1252)
- Strip BOM if present. Skip all-blank rows silently.

**ExcelParser:**
- Read Sheet 1 only. Engine: `openpyxl` for .xlsx, `xlrd` for .xls.
- Replace NaN → empty string. Cast all values to string. Drop fully empty rows.

**PDFParser:**
- Use `pdfplumber` to extract tables from all pages.
- Use the FIRST table with ≥ 2 columns and ≥ 1 data row.
- No table found → raise `ValueError("No data table found in PDF. The PDF must contain a selectable text table, not a scanned image.")`
- Strip currency symbols (`£ $ € ₹`) from numeric fields before returning rows.

### 6.4 Column Aliasing (flexible naming — resolve before validation)

```python
PRODUCT_ALIASES = {
    "sku":       ["sku", "product_code", "item_code", "barcode", "upc", "article_no"],
    "name":      ["name", "product_name", "item_name", "description"],
    "brand":     ["brand", "brand_name", "manufacturer"],
    "category":  ["category", "category_name", "dept", "department", "type"],
    "width_cm":  ["width_cm", "width", "w_cm"],
    "height_cm": ["height_cm", "height", "h_cm"],
    "depth_cm":  ["depth_cm", "depth", "d_cm"],
    "price":     ["price", "unit_price", "retail_price", "rrp", "mrp"],
}

SALES_ALIASES = {
    "sku":          ["sku", "product_code", "item_code", "barcode", "article_no"],
    "units_sold":   ["units_sold", "units", "qty", "quantity", "volume"],
    "revenue":      ["revenue", "sales", "net_sales", "gross_sales", "amount", "value"],
    "period_start": ["period_start", "start_date", "from_date", "date_from", "week_start"],
    "period_end":   ["period_end", "end_date", "to_date", "date_to", "week_end"],
}

STORE_ALIASES = {
    "store_name": ["store_name", "store", "outlet", "branch", "location_name", "name"],
    "city":       ["city", "town", "location"],
    "state":      ["state", "province", "region"],
    "store_type": ["store_type", "format", "type", "outlet_type"],
}
```

### 6.5 Validation Rules

**Product rows:**
- `sku` → REQUIRED, not empty. Trimmed + uppercased.
- `name` → REQUIRED, not empty.
- `width_cm`, `height_cm`, `depth_cm` → optional; must be > 0 if present.
- `price` → optional; must be ≥ 0 if present.
- Invalid optional fields → warning only, row still imported.

**Sales rows:**
- `sku` → REQUIRED.
- `revenue` → REQUIRED, must be ≥ 0.
- `units_sold` → optional; must be ≥ 0 integer if present.
- `period_start` / `period_end` → REQUIRED from row or query param override. period_end ≥ period_start.
- Accept date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `MM/DD/YYYY`, `DD-MM-YYYY`.
- Revenue/units with commas (`1,240`) or currency symbols (`₹48`) → strip and parse.

**Upsert behaviour:**
- Products: conflict on `(user_id, sku)` → UPDATE.
- Sales: conflict on `(store_id, sku, period_start, period_end)` → UPDATE.
- Stores: conflict on `(user_id, raw_name)` → UPDATE.

### 6.6 SKU Deduplicator (`backend/ingestion/sku_deduplicator.py`)

Runs during product import only, after validation, before DB upsert. Uses `rapidfuzz`.

```python
import re
from rapidfuzz import fuzz, process

STOPWORDS = {
    "ml", "gm", "gms", "g", "kg", "l", "ltr", "litre",
    "pack", "pck", "pcs", "piece", "pieces", "bottle", "can", "pouch",
    "box", "bag", "sachet", "tube", "jar",
    "new", "original", "classic", "regular", "special", "premium",
    "the", "a", "an", "of", "with",
}

def normalise_for_dedup(name: str) -> str:
    """
    Produce a deduplication key — used for fuzzy matching ONLY, never stored.
    1. Lowercase, remove punctuation (except hyphens)
    2. Tokenise, remove STOPWORDS
    3. Normalise adjacent quantity+unit pairs: "500 ml" → "500ml"
    4. Sort tokens alphabetically (so "Cola Coke" == "Coke Cola")
    5. Join with space
    """
    name = name.lower().strip()
    name = re.sub(r"[^\w\s\-]", " ", name)
    name = re.sub(r"\s+", " ", name)
    tokens = [t for t in name.split() if t not in STOPWORDS]

    normalised, i = [], 0
    while i < len(tokens):
        tok = tokens[i]
        if re.match(r"^\d+\.?\d*$", tok) and i + 1 < len(tokens) and tokens[i+1] in {"ml","l","ltr","g","gm","gms","kg"}:
            normalised.append(tok + tokens[i+1])
            i += 2
        else:
            normalised.append(tok)
            i += 1
    normalised.sort()
    return " ".join(normalised)


class SKUDeduplicator:
    """
    Flags potential duplicate products. NEVER blocks imports. Flags are informational.

    Threshold: 88 (fuzz.token_sort_ratio) — high enough to avoid false positives,
    low enough to catch Coca Cola / Coke / CC variants.
    """
    SIMILARITY_THRESHOLD = 88

    def find_duplicates(self, incoming_rows: list[dict], existing_products: list[dict]) -> list[dict]:
        """
        Returns list of DuplicateFlag dicts:
        {sku_a, name_a, sku_b, name_b, similarity, source: 'intra_file'|'cross_import'}

        Checks:
        1. Each incoming row vs other rows in the same file (intra_file)
        2. Each incoming row vs existing DB products (cross_import)

        One flag per row maximum — do not over-report.
        """
        flags = []
        existing_keys = {p["sku"]: normalise_for_dedup(p["name"]) for p in existing_products}
        seen_in_file = {}  # normalised_key → row_index

        for i, row in enumerate(incoming_rows):
            key = normalise_for_dedup(row.get("name", ""))
            sku = row.get("sku", "").upper().strip()

            # Intra-file check
            for prev_key, prev_idx in seen_in_file.items():
                score = fuzz.token_sort_ratio(key, prev_key)
                if score >= self.SIMILARITY_THRESHOLD:
                    prev = incoming_rows[prev_idx]
                    flags.append({
                        "row_a": prev_idx + 2, "sku_a": prev.get("sku",""), "name_a": prev.get("name",""),
                        "row_b": i + 2, "sku_b": sku, "name_b": row.get("name",""),
                        "similarity": score, "source": "intra_file"
                    })
                    break

            # Cross-import check
            if existing_keys:
                match = process.extractOne(key, existing_keys.values(),
                    scorer=fuzz.token_sort_ratio, score_cutoff=self.SIMILARITY_THRESHOLD)
                if match:
                    matched_sku = next(s for s, k in existing_keys.items() if k == match[0])
                    matched_name = next(p["name"] for p in existing_products if p["sku"] == matched_sku)
                    flags.append({
                        "row_a": None, "sku_a": matched_sku, "name_a": matched_name,
                        "row_b": i + 2, "sku_b": sku, "name_b": row.get("name",""),
                        "similarity": match[1], "source": "cross_import"
                    })

            seen_in_file[key] = i

        return flags
```

### 6.7 Import Summary Response

All import endpoints return this shape:

```json
{
  "import_id": "uuid",
  "import_type": "product",
  "file_format": "csv",
  "original_filename": "products_q1.csv",
  "imported_at": "2025-01-31T14:32:00Z",
  "total_rows": 120,
  "success": 115,
  "skipped": 2,
  "errors": [
    { "row": 14, "reason": "sku is required and must not be empty" },
    { "row": 67, "reason": "width_cm must be a number, got 'N/A'" }
  ],
  "status": "partial",
  "unmatched_skus": ["SKU-998", "SKU-999"],
  "potential_duplicates": [
    {
      "sku_a": "COKE-001", "name_a": "Coca Cola 500ml",
      "sku_b": "COKE-002", "name_b": "Coke 500 ML",
      "similarity": 91, "source": "intra_file"
    }
  ]
}
```

**Frontend `ImportSummaryCard.tsx`:** If `potential_duplicates.length > 0`, show a collapsible yellow warning section:
```
⚠️ Possible Duplicate Products Detected (2)
These SKUs may refer to the same product. Review manually.

| Existing           | Imported        | Match % |
| Coca Cola 500ml    | Coke 500 ML     | 91%     |
```
This is informational only. Both records are stored. Merge is Phase 2.

### 6.8 API Endpoints (Ingestion)

```
POST /api/v1/products/import              — multipart/form-data, field: "file"
POST /api/v1/sales/import                 — multipart + ?store_id + ?period_start + ?period_end
POST /api/v1/stores/import                — multipart/form-data, field: "file"
GET  /api/v1/products/import/history      — list ImportLog for current user
GET  /api/v1/sales/import/history?store_id=
```

---

## 7. LAYER 3 — DATA NORMALISATION

### 7.1 Product Normalisation

```python
CATEGORY_DEFAULTS = {
    "beverages":     (7.0,  22.0, 7.0),
    "dairy":         (8.0,  20.0, 8.0),
    "snacks":        (15.0, 18.0, 10.0),
    "personal care": (5.0,  18.0, 5.0),
    "household":     (12.0, 25.0, 12.0),
    "_default":      (10.0, 20.0, 10.0),
}

CATEGORY_KEYWORDS = {
    "beverages":     ["juice", "water", "soda", "cola", "drink", "milk", "tea", "coffee"],
    "snacks":        ["chips", "biscuit", "cookie", "cracker", "wafer", "namkeen"],
    "dairy":         ["cheese", "yogurt", "curd", "butter", "cream", "paneer"],
    "personal care": ["shampoo", "soap", "toothpaste", "deodorant", "lotion"],
    "household":     ["detergent", "cleaner", "dish", "fabric", "bleach"],
}

def normalise_product(row: dict) -> dict:
    """
    - SKU: strip, uppercase
    - Name: strip, title-case if all-uppercase
    - Category: strip, title-case. If empty → infer from CATEGORY_KEYWORDS scan of name
    - Brand: strip, title-case. If empty → leave None (do not infer)
    - Dimensions: if all None → apply CATEGORY_DEFAULTS for detected/inferred category
    """
```

### 7.2 Sales Normalisation

- SKU → uppercase, trim
- Revenue → round to 2 decimal places
- Units → cast to int; floor negatives to 0 (do not reject)
- Compute `revenue_per_unit = revenue / units_sold` if both present

---

## 8. LAYER 3.5 — ASSORTMENT FILTER (`backend/services/assortment_filter.py`)

**Purpose:** Determine which SKUs to pass to the planogram engine for a specific store.
Prevents overcrowded layouts by capping SKU count to what's realistic for the store type.

**NEVER return 0 included SKUs. If all filters would empty the list → return full catalogue with warning.**

```python
from dataclasses import dataclass

STORE_TYPE_SKU_LIMITS = {
    "supermarket":  150,
    "hypermarket":  300,
    "convenience":   50,
    "specialty":     80,
    "wholesale":    200,
    "unknown":      100,
}

@dataclass
class AssortmentResult:
    included_skus: list[str]    # SKUs passed to planogram engine
    excluded_skus: list[str]    # SKUs dropped
    filter_method: str          # 'sales_coverage' | 'top_n' | 'all'
    coverage_pct: float         # % of catalogue included
    message: str                # human-readable for UX


def filter_assortment(
    products: list[Product],
    sales: list[SalesData],
    store_type: str,
    shelf_count: int,
    shelf_width_cm: float,
) -> AssortmentResult:
    """
    Three cases, evaluated in order:

    CASE 1 — Sales data exists AND covers ≥ 20% of catalogue:
      included = only SKUs present in sales_data for this store
      filter_method = 'sales_coverage'

    CASE 2 — Sales data covers < 20% of catalogue:
      included = sales-covered SKUs + fill remaining slots alphabetically by category
      up to STORE_TYPE_SKU_LIMITS[store_type]
      filter_method = 'sales_coverage'
      Emit warning: "X% of your products have no sales data — remainder filled alphabetically"

    CASE 3 — No sales data at all:
      included = top N by price DESC (price as proxy for importance)
      N = STORE_TYPE_SKU_LIMITS[store_type]
      fallback to alphabetical if no price data
      filter_method = 'top_n'

    After case selection — apply shelf capacity cap:
      max_skus_by_shelf = floor((shelf_count * shelf_width_cm) / 10.0)
      (10cm = minimum product width assumption)
      trim from bottom of ranked list if over capacity
    """
```

---

## 9. LAYER 4 — STORE INTELLIGENCE ENGINE (`backend/services/store_intelligence.py`)

### 9.1 Purpose

Parse raw store names → structured hierarchy (country, state, city, locality, store_type)
with a `parse_confidence` score that feeds into planogram confidence scoring.

**Input:** `"RF Indiranagar BLR 560038"`
**Output:** `{ country, state, city, locality, store_type, detected_chain, pin_code, parse_confidence }`

**No external API calls. Pure Python lookup dictionaries only.**

### 9.2 Lookup Dictionaries (embed in module)

```python
CITY_ABBREVIATIONS = {
    "BLR": ("Bangalore", "Karnataka"),  "BLRU": ("Bangalore", "Karnataka"),
    "BNG": ("Bangalore", "Karnataka"),  "HYD":  ("Hyderabad", "Telangana"),
    "MUM": ("Mumbai", "Maharashtra"),   "BOM":  ("Mumbai", "Maharashtra"),
    "DEL": ("Delhi", "Delhi"),          "DLH":  ("Delhi", "Delhi"),
    "CHE": ("Chennai", "Tamil Nadu"),   "MAA":  ("Chennai", "Tamil Nadu"),
    "CCU": ("Kolkata", "West Bengal"),  "KOL":  ("Kolkata", "West Bengal"),
    "PNQ": ("Pune", "Maharashtra"),     "AMD":  ("Ahmedabad", "Gujarat"),
    "JAI": ("Jaipur", "Rajasthan"),     "LKO":  ("Lucknow", "Uttar Pradesh"),
    "IDR": ("Indore", "Madhya Pradesh"),"BPL":  ("Bhopal", "Madhya Pradesh"),
    "VZG": ("Visakhapatnam", "Andhra Pradesh"), "VIZ": ("Visakhapatnam", "Andhra Pradesh"),
    "SUR": ("Surat", "Gujarat"),        "NGP":  ("Nagpur", "Maharashtra"),
    "GZB": ("Ghaziabad", "Uttar Pradesh"),
}

CHAIN_ABBREVIATIONS = {
    "RF": "Reliance Fresh",   "RFH": "Reliance Fresh",
    "RS": "Reliance Smart",   "RSB": "Reliance Smart Bazaar",
    "DMT": "D-Mart",          "DMART": "D-Mart",
    "BB": "Big Bazaar",       "HV": "Heritage Fresh",
    "NTR": "Nature's Basket", "SL": "Spencer's",
    "MB": "More Supermarket", "MOB": "More Supermarket",
}

PIN_PREFIX_TO_STATE = {
    "110": "Delhi",       "400": "Maharashtra",  "411": "Maharashtra",
    "560": "Karnataka",   "561": "Karnataka",    "500": "Telangana",
    "600": "Tamil Nadu",  "700": "West Bengal",  "380": "Gujarat",
    "390": "Gujarat",     "302": "Rajasthan",    "226": "Uttar Pradesh",
    "452": "Madhya Pradesh", "462": "Madhya Pradesh",
    # ... extend to all major PIN prefixes
}

STORE_TYPE_KEYWORDS = {
    "supermarket": ["fresh", "mart", "super", "hypermarket", "bazaar", "bazar"],
    "convenience": ["express", "mini", "quick", "easy", "24"],
    "specialty":   ["pharmacy", "pharma", "electronics", "fashion", "beauty", "organic"],
    "wholesale":   ["cash", "carry", "wholesale", "depot"],
}

DIRECTION_WORDS = {
    "east", "west", "north", "south", "central", "main",
    "phase", "sector", "block", "unit", "shop", "no", "number",
    "new", "old", "upper", "lower", "outer", "inner",
}

INDIAN_CITIES = [
    ("mumbai", "Maharashtra"),     ("delhi", "Delhi"),
    ("bangalore", "Karnataka"),    ("bengaluru", "Karnataka"),
    ("hyderabad", "Telangana"),    ("chennai", "Tamil Nadu"),
    ("kolkata", "West Bengal"),    ("pune", "Maharashtra"),
    ("ahmedabad", "Gujarat"),      ("jaipur", "Rajasthan"),
    ("surat", "Gujarat"),          ("lucknow", "Uttar Pradesh"),
    ("nagpur", "Maharashtra"),     ("indore", "Madhya Pradesh"),
    ("bhopal", "Madhya Pradesh"),  ("visakhapatnam", "Andhra Pradesh"),
    ("patna", "Bihar"),            ("vadodara", "Gujarat"),
    # ... extend to 100+ cities
]
```

### 9.3 `parse()` Method — Full Algorithm

```python
import re

def extract_pin_code(raw_name: str) -> tuple[str | None, str]:
    """Extract 6-digit PIN (starts with 1-9). Returns (pin, cleaned_name)."""
    match = re.search(r"\b([1-9]\d{5})\b", raw_name)
    if match:
        return match.group(1), raw_name.replace(match.group(1), "").strip()
    return None, raw_name


def parse(self, raw_name: str) -> dict:
    """
    Step 0: Extract PIN code → remove from name, store separately
    Step 1: Tokenise; uppercase tokens for abbreviation lookup
    Step 2: Expand CHAIN_ABBREVIATIONS on first token (priority to brand prefix)
    Step 3: Expand CITY_ABBREVIATIONS on any token → set city + state
    Step 4: If city still None → scan word/bigrams against INDIAN_CITIES
    Step 5: Scan remaining tokens against INDIAN_STATES (explicit state in name)
    Step 6: Remove DIRECTION_WORDS from locality candidates
    Step 7: Detect store_type from STORE_TYPE_KEYWORDS (on full lowercased name)
    Step 8: If state still None AND pin found → infer from PIN_PREFIX_TO_STATE

    Compute parse_confidence:
      0.0 base
      +0.4 if city resolved
      +0.3 if state resolved
      +0.2 if store_type is not 'unknown'
      +0.1 if chain name expanded (brand known)
      Final: clamped to 0.0–1.0

    Returns:
    {
        "display_name": str,         # title-case of raw_name
        "country": "India",
        "state": str | None,
        "city": str | None,
        "locality": str | None,      # remaining tokens not matched as city/state/chain/direction
        "store_type": str,           # 'supermarket' if no match (default)
        "detected_chain": str | None,
        "pin_code": str | None,
        "parse_confidence": float,
    }

    NEVER raise. Always return best-effort result even if nothing matches.
    """
```

### 9.4 Hierarchy Builder

```python
def build_store_hierarchy(stores: list[Store]) -> dict:
    """
    Returns nested dict for navigation sidebar:
    {
        "India": {
            "Karnataka": {
                "Bangalore": [store_id_1, store_id_2],
                "Mysore":    [store_id_3],
            }
        }
    }
    Unresolved city  → "Unknown City"
    Unresolved state → "Unknown State"
    """
```

### 9.5 API Endpoints (Stores)

```
POST   /api/v1/stores
GET    /api/v1/stores
GET    /api/v1/stores/hierarchy
GET    /api/v1/stores/{store_id}
PUT    /api/v1/stores/{store_id}
DELETE /api/v1/stores/{store_id}
POST   /api/v1/stores/import
```

---

## 10. LAYER 5 — PLANOGRAM ENGINE (`backend/services/planogram_engine.py`)

> This is the most critical layer. Get it right.

### 10.1 Non-negotiable rules

- ALWAYS generate a planogram. Never block on missing data.
- Missing sales → rank alphabetically by category. Never refuse.
- Missing dimensions → use `CATEGORY_DEFAULTS`. Never refuse.
- Missing shelf config → use defaults: `width=180cm, height=200cm, 5 shelves`.
- `is_user_edited = true` → NEVER auto-regenerate without explicit user confirmation.

### 10.2 Generation Levels

| Level | Scope | Sales data used |
|-------|-------|----------------|
| `store` | Single store | Store's own sales_data |
| `city` | All stores in a city | Sum of all city stores' sales |
| `state` | All stores in a state | Sum of all state stores' sales |

### 10.3 Input Dataclass

```python
@dataclass
class PlanogramInput:
    store_id: UUID
    store: Store                   # full store record including store_type, parse_confidence
    generation_level: str          # 'store' | 'city' | 'state'
    products: list[Product]        # full user catalogue (assortment filter applied separately)
    sales: list[SalesData]         # may be empty
    shelf_count: int = 5
    shelf_width_cm: float = 180.0
    shelf_height_cm: float = 200.0
```

### 10.4 Store-Type Rules

```python
STORE_TYPE_RULES = {
    "supermarket": {
        "max_skus": 150, "max_facings": 4,
        "prioritise_by": "revenue",       # primary ranking metric
        "category_blocking": True,
        "eye_level_pct": 0.20,            # top X% of SKUs → eye-level shelf
        "low_level_categories": ["bulk", "household", "water", "oil"],
    },
    "convenience": {
        "max_skus": 50, "max_facings": 3,
        "prioritise_by": "units",         # convenience = turnover > revenue
        "category_blocking": True,
        "eye_level_pct": 0.30,
        "low_level_categories": ["household", "cleaning"],
    },
    "hypermarket": {
        "max_skus": 300, "max_facings": 6,
        "prioritise_by": "revenue",
        "category_blocking": True,
        "eye_level_pct": 0.15,
        "low_level_categories": ["bulk", "water", "rice", "flour", "oil"],
    },
    "specialty": {
        "max_skus": 80, "max_facings": 5,
        "prioritise_by": "revenue",
        "category_blocking": False,       # curated → less strict blocking
        "eye_level_pct": 0.25,
        "low_level_categories": [],
    },
    "wholesale": {
        "max_skus": 200, "max_facings": 2,
        "prioritise_by": "units",
        "category_blocking": True,
        "eye_level_pct": 0.20,
        "low_level_categories": [],
    },
    "_default": {
        "max_skus": 100, "max_facings": 3,
        "prioritise_by": "revenue",
        "category_blocking": True,
        "eye_level_pct": 0.20,
        "low_level_categories": [],
    },
}
```

### 10.5 `rank_skus()` — Store-Type Aware

```python
def rank_skus(products: list[Product], sales: list[SalesData], store_type: str) -> list[RankedSKU]:
    """
    rules = STORE_TYPE_RULES.get(store_type, STORE_TYPE_RULES["_default"])

    Sales score (if sales data exists):
      if rules["prioritise_by"] == "revenue":
        sales_score = (revenue/max_revenue * 0.7) + (units_sold/max_units * 0.3)
      if rules["prioritise_by"] == "units":
        sales_score = (units_sold/max_units * 0.7) + (revenue/max_revenue * 0.3)

    No sales data → sales_score = 0.0 for all

    Category rank:
      categories ordered by total revenue DESC (or alphabetical if no sales)
      SKUs within category ordered by sales_score DESC, then name ASC

    Final rank = category_rank ASC, then sales_score DESC, then name ASC

    Post-rank: force low_level_categories to low_level tier regardless of score
    (check if product.category keyword in rules["low_level_categories"])
    """

@dataclass
class RankedSKU:
    product: Product
    sales_score: float          # 0.0–1.0
    category_rank: int
    overall_rank: int
    suggested_facings: int
    placement_tier: str         # 'eye_level' | 'mid_level' | 'top_level' | 'low_level'
```

### 10.6 `calculate_facings()` — Store-Type Capped

```python
def calculate_facings(product: Product, sales_score: float, shelf_width_cm: float, store_type: str) -> int:
    """
    Base logic:
      sales_score > 0.7 → 3 facings
      sales_score > 0.4 → 2 facings
      else              → 1 facing

    Capacity cap: min(calculated, floor(shelf_width_cm / (product.width_cm or 10)))
    Store-type cap: min(result, STORE_TYPE_RULES[store_type]["max_facings"])
    Floor: always ≥ 1
    """
```

### 10.7 `assign_to_shelves()` — Store-Type Aware

```python
def assign_to_shelves(ranked_skus: list[RankedSKU], shelf_count: int,
                      shelf_width_cm: float, store_type: str) -> list[ShelfAssignment]:
    """
    rules = STORE_TYPE_RULES[store_type]

    Shelf tier mapping (shelf_count=5, 1=top):
      Shelf 1     → top_level   (least accessible)
      Shelf 2     → eye_level   (prime placement — top rules["eye_level_pct"] of SKUs)
      Shelves 3,4 → mid_level   (middle 50% of SKUs, split evenly)
      Shelf 5     → low_level   (floor level — low_level_categories forced here)

    Packing:
      Track remaining_width_cm per shelf
      space_needed = product.width_cm * suggested_facings
      If > remaining → reduce facings until fits → if 1 facing still too wide → next shelf
      If all shelves full → overflow to last shelf (flag in overflow_skus, allow slight overage)

    Category blocking:
      Adjacent SKUs of same category on same shelf where possible
      Never split one category across 3+ shelves
    """

@dataclass
class ShelfAssignment:
    shelf_number: int
    product_id: UUID
    sku: str
    position_x_cm: float
    facing_count: int
    placement_tier: str
```

### 10.8 Confidence Score

```python
def compute_confidence_score(
    products: list[Product],
    sales: list[SalesData],
    store_parse_confidence: float,   # from stores.parse_confidence
    assortment: AssortmentResult,
) -> ConfidenceScore:
    """
    Weighted composite score (0.0–1.0):
      Sales coverage    (40%): SKUs with revenue / total included SKUs
      Dimension coverage(30%): SKUs with width_cm AND height_cm / total
      Category coverage (15%): SKUs with non-empty category / total
      Store parse conf  (15%): stores.parse_confidence

    Tier:
      score >= 0.75 → 'high'   (data reliable, planogram trustworthy)
      score >= 0.45 → 'medium' (usable, some assumptions made)
      score <  0.45 → 'low'    (heavy assumptions — treat as draft)
    """

@dataclass
class ConfidenceScore:
    score: float
    tier: str               # 'high' | 'medium' | 'low'
    sales_coverage_pct: float
    dimension_coverage_pct: float
    category_coverage_pct: float
    store_parse_confidence: float
```

### 10.9 Data Quality Warnings

```python
def build_data_quality_warnings(
    confidence: ConfidenceScore,
    assortment: AssortmentResult,
    store: Store,
) -> list[DataQualityWarning]:
    """
    Generates structured warnings with deep-link action URLs.

    Rules:
      confidence.sales_coverage_pct < 50
        → code: "low_sales_coverage", severity: "high"
        → action_url: f"/stores/{store.id}/data?tab=import"

      confidence.dimension_coverage_pct < 40
        → code: "low_dimension_coverage", severity: "medium"
        → action_url: "/products?filter=missing_dimensions"

      confidence.category_coverage_pct < 60
        → code: "low_category_coverage", severity: "medium"
        → action_url: "/products?filter=missing_category"

      store.parse_confidence < 0.5
        → code: "store_location_uncertain", severity: "low"
        → action_url: f"/stores/{store.id}/edit"

      assortment.filter_method == "top_n"
        → code: "no_sales_assortment", severity: "high"
        → action_url: f"/stores/{store.id}/data?tab=import"
    """

@dataclass
class DataQualityWarning:
    code: str           # machine-readable key
    severity: str       # 'high' | 'medium' | 'low'
    message: str        # human-readable explanation
    action_label: str   # CTA button text
    action_url: str     # deep-link to fix the issue
```

### 10.10 `generate()` — Full Orchestration

```python
async def generate(input: PlanogramInput, db: AsyncSession) -> PlanogramJSON:
    """
    1. filter_assortment(input.products, input.sales, input.store.store_type, ...)
    2. filtered_products = [p for p in input.products if p.sku in assortment.included_skus]
    3. ranked = rank_skus(filtered_products, input.sales, input.store.store_type)
    4. assignments = assign_to_shelves(ranked, input.shelf_count, input.shelf_width_cm, input.store.store_type)
    5. confidence = compute_confidence_score(filtered_products, input.sales, input.store.parse_confidence, assortment)
    6. warnings = build_data_quality_warnings(confidence, assortment, input.store)
    7. return build_planogram_json(assignments, input, assortment, confidence, warnings)
    """
```

### 10.11 Color Assignment (deterministic)

```python
CATEGORY_COLORS = {
    "dairy":         "#4A90D9",
    "beverages":     "#7ED321",
    "snacks":        "#F5A623",
    "personal care": "#9B59B6",
    "household":     "#E74C3C",
    "bakery":        "#E67E22",
    "frozen":        "#1ABC9C",
    "_default":      "#95A5A6",
}

def get_product_color(category: str) -> str:
    key = category.lower().strip() if category else "_default"
    return CATEGORY_COLORS.get(key, CATEGORY_COLORS["_default"])
```

### 10.12 Multi-Level Generation

```python
async def generate_for_store(store_id: UUID, db: AsyncSession) -> Planogram:
    """Store-level: uses store's own sales_data."""

async def generate_for_city(city: str, state: str, user_id: UUID, db: AsyncSession) -> list[Planogram]:
    """Aggregate sales SUM across all city stores. Generate one template planogram.
       Apply to all city stores where is_user_edited = False."""

async def generate_for_state(state: str, user_id: UUID, db: AsyncSession) -> list[Planogram]:
    """Same as city but state-level aggregation."""
```

### 10.13 Canonical Planogram JSON Schema

This is the exact format stored in `planograms.planogram_json` and returned by all planogram endpoints:

```json
{
  "planogram_id": "uuid",
  "store_id": "uuid",
  "generation_level": "store",
  "generation_method": "auto",
  "generated_at": "2025-01-31T14:00:00Z",
  "has_sales_data": true,

  "confidence": {
    "score": 0.61,
    "tier": "medium",
    "sales_coverage_pct": 72.0,
    "dimension_coverage_pct": 45.0,
    "category_coverage_pct": 88.0,
    "store_parse_confidence": 0.70
  },

  "assortment": {
    "total_catalogue_skus": 320,
    "included_skus": 85,
    "excluded_skus": 235,
    "filter_method": "sales_coverage",
    "coverage_pct": 26.6,
    "message": "Showing 85 SKUs with sales data. 235 catalogue products excluded."
  },

  "data_quality_warnings": [
    {
      "code": "low_dimension_coverage",
      "severity": "medium",
      "message": "55% of products are missing dimensions. Default sizes used — shelf spacing may be inaccurate.",
      "action_label": "Add product dimensions",
      "action_url": "/products?filter=missing_dimensions"
    }
  ],

  "shelf_config": {
    "shelf_count": 5,
    "shelf_width_cm": 180.0,
    "shelf_height_cm": 200.0,
    "shelf_depth_cm": 40.0,
    "shelf_spacing_cm": 40.0,
    "store_type": "convenience",
    "store_type_rules_applied": true
  },

  "shelves": [
    {
      "shelf_number": 2,
      "tier": "eye_level",
      "remaining_width_cm": 12.5,
      "products": [
        {
          "product_id": "uuid",
          "sku": "SKU-001",
          "name": "Organic Milk 1L",
          "brand": "DairyBest",
          "category": "Dairy",
          "position_x_cm": 0.0,
          "width_cm": 7.5,
          "height_cm": 23.0,
          "facing_count": 3,
          "total_width_cm": 22.5,
          "sales_score": 0.87,
          "revenue": 48000.0,
          "units_sold": 240,
          "placement_tier": "eye_level",
          "color_hex": "#4A90D9"
        }
      ]
    }
  ],

  "overflow_skus": [],

  "category_summary": {
    "Dairy": { "sku_count": 5, "total_revenue": 120000, "shelves": [2, 3] },
    "Beverages": { "sku_count": 8, "total_revenue": 95000, "shelves": [3, 4] }
  }
}
```

### 10.14 API Endpoints (Planograms)

```
POST   /api/v1/planograms/generate
         Body: { store_id, generation_level, shelf_count?, shelf_width_cm?, shelf_height_cm? }
POST   /api/v1/planograms/generate-all
         Body: { level: "city" | "state" }
GET    /api/v1/planograms/{planogram_id}
GET    /api/v1/planograms?store_id=
PUT    /api/v1/planograms/{planogram_id}   → sets is_user_edited=true, snapshots version
DELETE /api/v1/planograms/{planogram_id}
GET    /api/v1/planograms/{planogram_id}/versions
POST   /api/v1/planograms/{planogram_id}/rollback/{version_id}
GET    /api/v1/planograms/{planogram_id}/export/jpeg
GET    /api/v1/planograms/{planogram_id}/export/pptx
```

---

## 11. LAYER 6 — VISUAL EDITOR (Konva.js)

### 11.1 Canvas Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ TOP BAR: [Store Name + Hierarchy]  [Confidence Badge]  [Regenerate]  │
│          [Save]  [Export ▼]                                          │
├─────────────┬────────────────────────────────────────────────────────┤
│             │ DATA QUALITY BANNER (if warnings.length > 0)           │
│ LEFT PANEL  ├────────────────────────────────────────────────────────┤
│             │                                                         │
│ SKU List    │          PLANOGRAM CANVAS (Konva Stage)                │
│ (draggable) │                                                         │
│             │   [ Shelf 1 — Top Level  ]                             │
│ Filter by:  │   [ Shelf 2 — Eye Level  ] ← prime placement          │
│  category   │   [ Shelf 3 — Mid Level  ]                             │
│  brand      │   [ Shelf 4 — Mid Level  ]                             │
│  search     │   [ Shelf 5 — Low Level  ]                             │
│             │                                                         │
├─────────────┴────────────────────────────────────────────────────────┤
│ BOTTOM: Category legend  |  SKU count  |  Data freshness             │
└──────────────────────────────────────────────────────────────────────┘
```

### 11.2 Konva Components

**`PlanogramCanvas.tsx`** — Konva `Stage` + 2 layers:
- `GridLayer` — shelf lines (horizontal, static, not re-rendered on updates)
- `ProductLayer` — one `ProductBlock` per product×facing

**`ProductBlock.tsx`:**
- Fill: `color_hex`; width: `(width_cm / shelf_width_cm) * canvas_px_width * facing_count`
- Draggable. On `dragend` → update `position_x_cm` or `shelf_number` → call `PUT /api/v1/planograms/{id}`
- Optimistic update: update Zustand immediately, sync in background

**`FacingControls.tsx`** — on product click: `+`/`−` buttons, capacity bar per shelf

**`ProductPanel.tsx`** — left sidebar: all catalogue products, search + filter, drag to add

**`RegenerateButton`** — warns if `is_user_edited = true`: "This will overwrite your edits. Continue?"

### 11.3 Confidence UX (`ConfidenceBadge.tsx`)

```typescript
/**
 * Shown in top-right of planogram canvas top bar.
 *
 * HIGH   → green   "✅ High Confidence"    — no extra action
 * MEDIUM → yellow  "⚠️ Medium Confidence"  — tooltip on hover with breakdown
 * LOW    → red     "⚠️ Low Confidence · Draft only"
 *                  + non-dismissible banner below top bar
 *
 * Clicking badge opens ConfidenceBreakdownPanel (right drawer):
 *   Sales data:     72%  [████████░░]
 *   Dimensions:     45%  [████░░░░░░]
 *   Categories:     88%  [█████████░]
 *   Store accuracy: 70%  [███████░░░]
 *   [→ Upload sales data]
 *   [→ Add product dimensions]
 */
```

### 11.4 Data Quality UX (`DataQualityBanner.tsx`)

```typescript
/**
 * Shown below top bar if data_quality_warnings.length > 0.
 *
 * HIGH severity   → persistent amber/red banner, cannot be dismissed
 * MEDIUM/LOW      → dismissible info strip
 *
 * Each warning renders as:
 *  ┌─────────────────────────────────────────────────────────┐
 *  │ ⚠️ [message]                           [action_label →] │
 *  └─────────────────────────────────────────────────────────┘
 * action_label → router.push(action_url)
 * High severity at top, low at bottom.
 */
```

### 11.5 Zustand `planogramStore`

```typescript
interface PlanogramStore {
  planogram: PlanogramJSON | null
  isDirty: boolean
  isSaving: boolean
  selectedProductSku: string | null
  setPlanogram: (p: PlanogramJSON) => void
  moveProduct: (sku: string, toShelf: number, newPositionX: number) => void
  updateFacings: (sku: string, shelfNumber: number, facingCount: number) => void
  addProduct: (product: Product, toShelf: number) => void
  removeProduct: (sku: string, shelfNumber: number) => void
  savePlanogram: (planogramId: string) => Promise<void>
  setSelected: (sku: string | null) => void
  markDirty: () => void
  markSaved: () => void
}
```

---

## 12. LAYER 7 — EXPORT ENGINE

### 12.1 JPEG Export (`GET /api/v1/planograms/{id}/export/jpeg`)

```python
from PIL import Image, ImageDraw, ImageFont

def render_planogram_to_jpeg(planogram: PlanogramJSON) -> bytes:
    """
    Canvas: 1800 × 1200 px, white background

    Header (top 80px):
      Store name + generation level + "Generated by Eureka" + date

    Shelf area:
      Shelf lines: light grey #CCCCCC, 2px horizontal
      Shelf labels left margin: "Shelf 2 — Eye Level"

    Each product block:
      x   = (position_x_cm / shelf_config.shelf_width_cm) * canvas_width
      w   = (total_width_cm / shelf_config.shelf_width_cm) * canvas_width
      y   = header_height + (shelf_number - 1) * shelf_height_px
      h   = shelf_height_px - 4px padding
      Fill: color_hex
      Border: black 1px
      Text line 1: SKU (small, bold) — white if dark fill, black if light fill
      Text line 2: name (smaller, truncated)

    Footer (bottom 60px):
      Category legend: color swatch + category name for each category
      "Data as of: {last_sales_date}" | Confidence: {tier}

    Confidence watermark (if tier == 'low'):
      Light red diagonal text: "DRAFT — Low Confidence"

    Output: JPEG bytes at quality=92
    """
```

### 12.2 PPTX Export (`GET /api/v1/planograms/{id}/export/pptx`)

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def render_planogram_to_pptx(planogram: PlanogramJSON) -> bytes:
    """
    Slide dimensions: 13.33" × 7.5" (widescreen 16:9)

    Slide 1 — Title:
      Background: dark navy #1A2332, text: white
      Title: store display name + generation level
      Subtitle: "Planogram | Generated by Eureka | {date}"
      Confidence badge in corner: tier + score

    Slide 2 — Planogram Visual:
      Each product = filled Rectangle shape (color_hex fill, thin black border)
      Text: SKU bold + "\n" + product name (small)
      Shelf dividers = horizontal lines
      Shelf tier labels on left margin

    Slide 3 — Summary:
      Table: Category | SKU Count | Total Revenue | Shelves
      Top 10 SKUs by revenue (if available)
      Data quality warnings listed
      Assortment summary: "Showing X of Y catalogue SKUs"

    Output: PPTX bytes
    """
```

### 12.3 Export Frontend (`ExportMenu.tsx`)

```typescript
// Dropdown in top bar: [Export ▼]
//   → Export as JPEG      → GET /export/jpeg → download as "{store}_{date}_planogram.jpg"
//   → Export as PowerPoint → GET /export/pptx → download as "{store}_{date}_planogram.pptx"
// Show spinner while generating. Show error toast on failure.
```

---

## 13. FRONTEND ROUTES

```
/                                  → Landing / Login
/dashboard                         → Store hierarchy tree + DataHealthWidget per store
/upload                            → Upload hub: Products | Sales | Stores tabs
/stores                            → Full store list table with hierarchy columns
/stores/{id}                       → Store detail + planogram list
/stores/{id}/planogram/{pid}       → Planogram visual editor
/stores/{id}/analytics             → Analytics dashboard
/products                          → Product catalogue CRUD + import
/settings                          → User account settings
```

**`/dashboard`:**
- Collapsible hierarchy tree: Country → State → City → Store
- `DataHealthWidget.tsx` per store:
  ```
  [Sales data]  ████░░░░░░  28%
  [Dimensions]  ██████░░░░  58%
  [Categories]  █████████░  91%
  ```
  Any metric < 50% → "Improve data →" CTA
- "Generate All Planograms" button (city or state level)

**`/upload`:** Three tabs: Products | Sales | Stores. Each has `FileUploader`, format guide, sample CSV download, `ImportSummaryCard` after upload.

**`/products?filter=missing_dimensions`:** Show only products where `width_cm IS NULL`. Filter banner: "Showing X products missing dimensions. Update them to improve planogram accuracy."

**`/products?filter=missing_category`:** Show only products where `category IS NULL OR category = ''`.

---

## 14. COMPLETE API REFERENCE

```
AUTH
  POST   /api/v1/auth/register
  POST   /api/v1/auth/login
  POST   /api/v1/auth/refresh

STORES
  POST   /api/v1/stores
  GET    /api/v1/stores
  GET    /api/v1/stores/hierarchy
  GET    /api/v1/stores/{store_id}
  PUT    /api/v1/stores/{store_id}
  DELETE /api/v1/stores/{store_id}
  POST   /api/v1/stores/import

PRODUCTS
  POST   /api/v1/products
  GET    /api/v1/products                       ?filter=missing_dimensions|missing_category
  PUT    /api/v1/products/{product_id}
  DELETE /api/v1/products/{product_id}
  POST   /api/v1/products/import
  GET    /api/v1/products/import/history

SALES
  POST   /api/v1/sales
  GET    /api/v1/sales?store_id=
  PUT    /api/v1/sales/{sales_id}
  DELETE /api/v1/sales/{sales_id}
  POST   /api/v1/sales/import                   ?store_id + ?period_start + ?period_end
  GET    /api/v1/sales/import/history?store_id=

PLANOGRAMS
  POST   /api/v1/planograms/generate
  POST   /api/v1/planograms/generate-all
  GET    /api/v1/planograms/{planogram_id}
  GET    /api/v1/planograms?store_id=
  PUT    /api/v1/planograms/{planogram_id}
  DELETE /api/v1/planograms/{planogram_id}
  GET    /api/v1/planograms/{planogram_id}/versions
  POST   /api/v1/planograms/{planogram_id}/rollback/{version_id}
  GET    /api/v1/planograms/{planogram_id}/export/jpeg
  GET    /api/v1/planograms/{planogram_id}/export/pptx

ANALYTICS
  GET    /api/v1/analytics/{store_id}/overview
  GET    /api/v1/analytics/{store_id}/skus
  GET    /api/v1/analytics/{store_id}/categories
```

---

## 15. PROJECT STRUCTURE

```
eureka/
├── frontend/
│   ├── app/
│   │   ├── (auth)/login/page.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── upload/page.tsx
│   │   ├── stores/page.tsx
│   │   ├── stores/[id]/page.tsx
│   │   ├── stores/[id]/planogram/[pid]/page.tsx
│   │   ├── stores/[id]/analytics/page.tsx
│   │   └── products/page.tsx
│   ├── components/
│   │   ├── planogram/
│   │   │   ├── PlanogramCanvas.tsx
│   │   │   ├── ProductBlock.tsx
│   │   │   ├── FacingControls.tsx
│   │   │   ├── ProductPanel.tsx
│   │   │   ├── RegenerateButton.tsx
│   │   │   ├── ExportMenu.tsx
│   │   │   ├── ConfidenceBadge.tsx        ← confidence tier display
│   │   │   └── DataQualityBanner.tsx      ← structured warning banners
│   │   ├── ingestion/
│   │   │   ├── FileUploader.tsx
│   │   │   ├── ImportSummaryCard.tsx      ← includes potential_duplicates section
│   │   │   └── ImportHistory.tsx
│   │   ├── stores/
│   │   │   ├── HierarchyTree.tsx
│   │   │   └── StoreCard.tsx
│   │   ├── dashboard/
│   │   │   └── DataHealthWidget.tsx       ← 3-bar data quality per store
│   │   └── analytics/
│   │       ├── SkuRankingTable.tsx
│   │       └── DataFreshnessIndicator.tsx
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── planogramStore.ts
│   │   └── productStore.ts
│   └── lib/
│       └── api.ts
│
├── backend/
│   ├── main.py
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── stores.py
│   │   ├── products.py
│   │   ├── products_import.py
│   │   ├── sales.py
│   │   ├── sales_import.py
│   │   ├── planograms.py
│   │   ├── planogram_export.py
│   │   └── analytics.py
│   ├── models/
│   │   ├── user.py
│   │   ├── store.py
│   │   ├── product.py
│   │   ├── sales_data.py
│   │   ├── planogram.py
│   │   └── import_log.py
│   ├── schemas/
│   ├── services/
│   │   ├── store_intelligence.py          ← Layer 4: parse + hierarchy
│   │   ├── assortment_filter.py           ← Layer 3.5: SKU filtering
│   │   ├── planogram_engine.py            ← Layer 5: full orchestration
│   │   ├── export_service.py              ← Layer 7: JPEG + PPTX
│   │   └── analytics_service.py
│   ├── ingestion/
│   │   ├── file_detector.py
│   │   ├── sku_deduplicator.py            ← Fix: fuzzy duplicate detection
│   │   ├── parsers/
│   │   │   ├── base_parser.py
│   │   │   ├── csv_parser.py
│   │   │   ├── excel_parser.py
│   │   │   └── pdf_parser.py
│   │   ├── validators/
│   │   │   ├── base_validator.py
│   │   │   ├── product_validator.py
│   │   │   └── sales_validator.py
│   │   ├── ingestion_service.py
│   │   └── storage_service.py
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   └── alembic/versions/
│
├── docker-compose.yml
└── .env.example
```

---

## 16. ENVIRONMENT VARIABLES

```bash
DATABASE_URL=postgresql+asyncpg://eureka:eureka@postgres:5432/eureka_db
SECRET_KEY=minimum-32-character-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
USE_LOCAL_STORAGE=true
LOCAL_UPLOAD_DIR=/app/uploads
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-south-1
S3_BUCKET_NAME=eureka-uploads
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 17. TESTING REQUIREMENTS

| Layer | What to test |
|-------|-------------|
| File Detection | Correct MIME detection from bytes; rejects wrong types, oversized, empty files |
| Parsers | Valid files; malformed rows; BOM/encoding edge cases; blank rows; scanned PDFs |
| Validators | All required/optional rules; numeric + date parsing; alias resolution |
| SKU Deduplicator | Coke/Coca Cola match; "500ml" vs "500 ML"; no false positives below threshold; intra-file + cross-import |
| Store Intelligence | Known city; abbreviation (BLR→Bangalore); PIN code; chain abbreviation (RF→Reliance Fresh); direction words stripped; completely unknown name → graceful fallback |
| Assortment Filter | With full sales; with no sales; with < 20% sales coverage; shelf capacity cap; never returns 0 SKUs |
| Planogram Engine | No sales → alphabetical; partial sales; store_type rules applied (convenience vs supermarket); eye_level_pct; low_level_categories forced bottom; shelf overflow handled |
| Confidence Score | All 4 dimensions compute correctly; tier boundaries (0.45, 0.75) |
| Data Quality Warnings | Each warning code triggered at correct threshold; action_url correct |
| Export JPEG | Valid JPEG bytes; correct dimensions; all shelves present; draft watermark if confidence=low |
| Export PPTX | Valid PPTX; 3 slides; shapes for all products; summary slide data |
| API Auth | All protected endpoints → 401 without token |
| Multi-tenancy | User A cannot read/edit User B's stores, products, planograms |

---

## 18. HARD CONSTRAINTS (NEVER VIOLATE)

1. **Never block planogram generation due to missing data.** Use defaults and proceed.
2. **Never overwrite `is_user_edited = true` planogram automatically.** Always warn first.
3. **Never trust the file's `Content-Type` header.** Detect format from bytes via `python-magic`.
4. **Never make outbound HTTP calls from the backend.** Zero external API calls.
5. **Never abort an import because of bad rows.** Partial import: commit valid rows, log errors.
6. **Never use synchronous SQLAlchemy calls.** All DB operations: `await db.execute(...)`.
7. **Never hardcode secrets.** All config from environment variables.
8. **All queries must filter by `user_id`.** Multi-tenant isolation at ORM level.
9. **SKU Deduplicator never blocks imports.** Flags are informational only. Merge = Phase 2.
10. **AssortmentFilter never returns 0 SKUs.** If everything filtered → return full catalogue with warning.

---

## 19. DO NOT BUILD (OUT OF SCOPE FOR PILOT)

- ML models of any kind
- Real-time data connectors (POS, ERP, WMS)
- WebSocket collaboration
- Computer vision / shelf image recognition
- Background job queues (Celery, Redis)
- Multi-store sync dashboard
- Supplier portal
- Demand forecasting or stockout prediction
- A/B testing
- Prompt-to-planogram (future)
- OCR for scanned/image PDFs
- Multi-sheet Excel parsing
- SKU merge UI (Phase 2 — deduplicator flags only)

---

## 20. IMPLEMENTATION ORDER

Build and test each layer fully before starting the next:

```
1. Auth (JWT, register, login, refresh)
2. File Ingestion:
     File Detection → CSV/Excel/PDF Parsers → Column Normaliser
     → Validators → SKU Deduplicator → Upsert → Archive → Import Log
3. Data Normalisation (product + sales normaliser, category inference, dimension defaults)
4. Store Intelligence Engine:
     PIN extractor → Abbreviation expansion → City/state matching → Hierarchy builder
   Layer 3.5: Assortment Filter
5. Planogram Engine:
     STORE_TYPE_RULES → rank_skus → calculate_facings → assign_to_shelves
     → compute_confidence_score → build_data_quality_warnings → build_planogram_json
6. Visual Editor:
     Konva canvas → ProductBlocks → drag/drop → FacingControls
     → ConfidenceBadge → DataQualityBanner → DataHealthWidget (dashboard)
7. Export Engine (JPEG → PPTX)
```

---

## 🔥 FINAL RULE

When there is any tradeoff between:

- **Data correctness** vs **generating a planogram** → generate the planogram
- **Perfect validation** vs **speed** → prioritise speed
- **Blocking on errors** vs **partial success** → always partial success
- **Complex logic** vs **simple logic that ships** → ship the simple version

> A planogram with imperfect data is infinitely more useful than a perfect system that never outputs anything.