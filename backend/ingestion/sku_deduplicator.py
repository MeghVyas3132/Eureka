import re
from collections import defaultdict
from typing import Any

from rapidfuzz import fuzz, process

STOPWORDS = {
    "ml",
    "gm",
    "gms",
    "g",
    "kg",
    "l",
    "ltr",
    "litre",
    "pack",
    "pck",
    "pcs",
    "piece",
    "pieces",
    "bottle",
    "can",
    "pouch",
    "box",
    "bag",
    "sachet",
    "tube",
    "jar",
    "new",
    "original",
    "classic",
    "regular",
    "special",
    "premium",
    "the",
    "a",
    "an",
    "of",
    "with",
}

UNIT_TOKENS = {"ml", "l", "ltr", "g", "gm", "gms", "kg"}


def normalise_for_dedup(name: str) -> str:
    """Build a fuzzy-matching key used only for duplicate detection."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s\-]", " ", name)
    name = re.sub(r"\s+", " ", name)

    tokens = [t for t in name.split() if t and t not in STOPWORDS]

    normalised: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if re.match(r"^\d+\.?\d*$", tok) and i + 1 < len(tokens) and tokens[i + 1] in UNIT_TOKENS:
            normalised.append(f"{tok}{tokens[i + 1]}")
            i += 2
            continue
        normalised.append(tok)
        i += 1

    normalised.sort()
    return " ".join(normalised)


class SKUDeduplicator:
    """Flags likely duplicates for imports. Informational only."""

    SIMILARITY_THRESHOLD = 88

    def find_duplicates(
        self,
        incoming_rows: list[dict[str, Any]],
        existing_products: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        flags: list[dict[str, Any]] = []

        existing_key_by_sku: dict[str, str] = {}
        existing_name_by_sku: dict[str, str] = {}
        existing_skus_by_key: dict[str, list[str]] = defaultdict(list)

        for product in existing_products:
            raw_sku = str(product.get("sku") or "").strip().upper()
            raw_name = str(product.get("name") or "").strip()
            if not raw_sku or not raw_name:
                continue
            key = normalise_for_dedup(raw_name)
            if not key:
                continue
            existing_key_by_sku[raw_sku] = key
            existing_name_by_sku[raw_sku] = raw_name
            existing_skus_by_key[key].append(raw_sku)

        existing_keys = list(existing_skus_by_key.keys())

        seen_in_file: dict[str, int] = {}

        for i, row in enumerate(incoming_rows):
            sku = str(row.get("sku") or "").strip().upper()
            name = str(row.get("name") or "").strip()
            if not sku or not name:
                continue

            key = normalise_for_dedup(name)
            if not key:
                continue

            row_flagged = False

            if seen_in_file:
                match = process.extractOne(
                    key,
                    seen_in_file.keys(),
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=self.SIMILARITY_THRESHOLD,
                )
                if match:
                    matched_key = str(match[0])
                    score = float(match[1])
                    prev_idx = seen_in_file[matched_key]
                    prev = incoming_rows[prev_idx]
                    flags.append(
                        {
                            "row_a": prev_idx + 2,
                            "sku_a": str(prev.get("sku") or "").strip().upper(),
                            "name_a": str(prev.get("name") or "").strip(),
                            "row_b": i + 2,
                            "sku_b": sku,
                            "name_b": name,
                            "similarity": round(score, 2),
                            "source": "intra_file",
                        }
                    )
                    row_flagged = True

            if not row_flagged and existing_keys:
                match = process.extractOne(
                    key,
                    existing_keys,
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=self.SIMILARITY_THRESHOLD,
                )
                if match:
                    matched_key = str(match[0])
                    score = float(match[1])
                    matched_sku = existing_skus_by_key[matched_key][0]
                    flags.append(
                        {
                            "row_a": None,
                            "sku_a": matched_sku,
                            "name_a": existing_name_by_sku.get(matched_sku, ""),
                            "row_b": i + 2,
                            "sku_b": sku,
                            "name_b": name,
                            "similarity": round(score, 2),
                            "source": "cross_import",
                        }
                    )

            seen_in_file[key] = i

        return flags
