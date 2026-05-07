from __future__ import annotations

import re
from typing import Any

CITY_ABBREVIATIONS = {
    "BLR": ("Bangalore", "Karnataka"),
    "BLRU": ("Bangalore", "Karnataka"),
    "BNG": ("Bangalore", "Karnataka"),
    "HYD": ("Hyderabad", "Telangana"),
    "MUM": ("Mumbai", "Maharashtra"),
    "BOM": ("Mumbai", "Maharashtra"),
    "DEL": ("Delhi", "Delhi"),
    "DLH": ("Delhi", "Delhi"),
    "CHE": ("Chennai", "Tamil Nadu"),
    "MAA": ("Chennai", "Tamil Nadu"),
    "CCU": ("Kolkata", "West Bengal"),
    "KOL": ("Kolkata", "West Bengal"),
    "PNQ": ("Pune", "Maharashtra"),
    "AMD": ("Ahmedabad", "Gujarat"),
    "JAI": ("Jaipur", "Rajasthan"),
    "LKO": ("Lucknow", "Uttar Pradesh"),
    "IDR": ("Indore", "Madhya Pradesh"),
    "BPL": ("Bhopal", "Madhya Pradesh"),
    "VZG": ("Visakhapatnam", "Andhra Pradesh"),
    "VIZ": ("Visakhapatnam", "Andhra Pradesh"),
    "SUR": ("Surat", "Gujarat"),
    "NGP": ("Nagpur", "Maharashtra"),
    "GZB": ("Ghaziabad", "Uttar Pradesh"),
}

CHAIN_ABBREVIATIONS = {
    "RF": "Reliance Fresh",
    "RFH": "Reliance Fresh",
    "RS": "Reliance Smart",
    "RSB": "Reliance Smart Bazaar",
    "DMT": "D-Mart",
    "DMART": "D-Mart",
    "BB": "Big Bazaar",
    "HV": "Heritage Fresh",
    "NTR": "Nature's Basket",
    "SL": "Spencer's",
    "MB": "More Supermarket",
    "MOB": "More Supermarket",
}

PIN_PREFIX_TO_STATE = {
    "110": "Delhi",
    "400": "Maharashtra",
    "411": "Maharashtra",
    "560": "Karnataka",
    "561": "Karnataka",
    "500": "Telangana",
    "600": "Tamil Nadu",
    "700": "West Bengal",
    "380": "Gujarat",
    "390": "Gujarat",
    "302": "Rajasthan",
    "226": "Uttar Pradesh",
    "452": "Madhya Pradesh",
    "462": "Madhya Pradesh",
}

STORE_TYPE_KEYWORDS = {
    "supermarket": ["fresh", "mart", "super", "hypermarket", "bazaar", "bazar"],
    "convenience": ["express", "mini", "quick", "easy", "24"],
    "specialty": ["pharmacy", "pharma", "electronics", "fashion", "beauty", "organic"],
    "wholesale": ["cash", "carry", "wholesale", "depot"],
}

DIRECTION_WORDS = {
    "east",
    "west",
    "north",
    "south",
    "central",
    "main",
    "phase",
    "sector",
    "block",
    "unit",
    "shop",
    "no",
    "number",
    "new",
    "old",
    "upper",
    "lower",
    "outer",
    "inner",
}

INDIAN_CITIES = [
    ("mumbai", "Maharashtra"),
    ("delhi", "Delhi"),
    ("bangalore", "Karnataka"),
    ("bengaluru", "Karnataka"),
    ("hyderabad", "Telangana"),
    ("chennai", "Tamil Nadu"),
    ("kolkata", "West Bengal"),
    ("pune", "Maharashtra"),
    ("ahmedabad", "Gujarat"),
    ("jaipur", "Rajasthan"),
    ("surat", "Gujarat"),
    ("lucknow", "Uttar Pradesh"),
    ("nagpur", "Maharashtra"),
    ("indore", "Madhya Pradesh"),
    ("bhopal", "Madhya Pradesh"),
    ("visakhapatnam", "Andhra Pradesh"),
    ("patna", "Bihar"),
    ("vadodara", "Gujarat"),
]

INDIAN_STATES = {
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chhattisgarh",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jharkhand",
    "karnataka",
    "kerala",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal",
    "delhi",
}


def extract_pin_code(raw_name: str) -> tuple[str | None, str]:
    match = re.search(r"\b([1-9]\d{5})\b", raw_name)
    if not match:
        return None, raw_name

    pin = match.group(1)
    cleaned = raw_name.replace(pin, " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return pin, cleaned


def _normalise_city_name(city: str) -> str:
    if city.lower() == "bengaluru":
        return "Bangalore"
    return city.title()


def _detect_store_type(raw_name_lower: str) -> tuple[str, bool]:
    for store_type, keywords in STORE_TYPE_KEYWORDS.items():
        if any(keyword in raw_name_lower for keyword in keywords):
            return store_type, True
    return "supermarket", False


def _build_locality(tokens: list[str], ignored_indexes: set[int], ignored_values: set[str]) -> str | None:
    locality_parts: list[str] = []
    for index, token in enumerate(tokens):
        lower = token.lower()
        if index in ignored_indexes:
            continue
        if lower in DIRECTION_WORDS:
            continue
        if lower in ignored_values:
            continue
        if re.fullmatch(r"\d+", token):
            continue
        locality_parts.append(token.title())

    if not locality_parts:
        return None
    return " ".join(locality_parts)


class StoreIntelligenceEngine:
    """Best-effort parser for noisy retail store names."""

    def parse(self, raw_name: str) -> dict[str, Any]:
        raw_name = (raw_name or "").strip()
        if not raw_name:
            return {
                "display_name": "",
                "country": "India",
                "state": None,
                "city": None,
                "locality": None,
                "store_type": "supermarket",
                "detected_chain": None,
                "pin_code": None,
                "parse_confidence": 0.0,
            }

        pin_code, name_without_pin = extract_pin_code(raw_name)
        tokens = re.findall(r"[A-Za-z0-9']+", name_without_pin)
        upper_tokens = [token.upper() for token in tokens]
        lower_tokens = [token.lower() for token in tokens]

        ignored_indexes: set[int] = set()
        ignored_values: set[str] = set()

        detected_chain: str | None = None
        if upper_tokens:
            chain = CHAIN_ABBREVIATIONS.get(upper_tokens[0])
            if chain:
                detected_chain = chain
                ignored_indexes.add(0)
                ignored_values.update({part.lower() for part in re.findall(r"[A-Za-z0-9']+", chain)})

        city: str | None = None
        state: str | None = None

        for idx, token in enumerate(upper_tokens):
            if token in CITY_ABBREVIATIONS:
                city, state = CITY_ABBREVIATIONS[token]
                ignored_indexes.add(idx)
                ignored_values.add(token.lower())
                break

        if not city:
            joined = " ".join(lower_tokens)
            for city_name, mapped_state in INDIAN_CITIES:
                if re.search(rf"\b{re.escape(city_name)}\b", joined):
                    city = _normalise_city_name(city_name)
                    state = mapped_state
                    for idx, token in enumerate(lower_tokens):
                        if token == city_name:
                            ignored_indexes.add(idx)
                    ignored_values.add(city_name)
                    break

        if not state:
            for idx, token in enumerate(lower_tokens):
                if token in INDIAN_STATES:
                    state = token.title()
                    ignored_indexes.add(idx)
                    ignored_values.add(token)
                    break
                if idx + 1 < len(lower_tokens):
                    two_word = f"{token} {lower_tokens[idx + 1]}"
                    if two_word in INDIAN_STATES:
                        state = two_word.title()
                        ignored_indexes.update({idx, idx + 1})
                        ignored_values.update({token, lower_tokens[idx + 1], two_word})
                        break

        if not state and pin_code:
            state = PIN_PREFIX_TO_STATE.get(pin_code[:3])

        store_type, store_type_detected = _detect_store_type(name_without_pin.lower())
        locality = _build_locality(tokens, ignored_indexes, ignored_values)

        parse_confidence = 0.0
        if city:
            parse_confidence += 0.4
        if state:
            parse_confidence += 0.3
        if store_type_detected:
            parse_confidence += 0.2
        if detected_chain:
            parse_confidence += 0.1
        parse_confidence = min(1.0, round(parse_confidence, 2))

        return {
            "display_name": raw_name.title(),
            "country": "India",
            "state": state,
            "city": city,
            "locality": locality,
            "store_type": store_type,
            "detected_chain": detected_chain,
            "pin_code": pin_code,
            "parse_confidence": parse_confidence,
        }


def build_store_hierarchy(stores: list[Any]) -> dict[str, dict[str, dict[str, list[str]]]]:
    hierarchy: dict[str, dict[str, dict[str, list[str]]]] = {}

    for store in stores:
        country = getattr(store, "country", None) or "India"
        state = getattr(store, "state", None) or "Unknown State"
        city = getattr(store, "city", None) or "Unknown City"

        hierarchy.setdefault(country, {})
        hierarchy[country].setdefault(state, {})
        hierarchy[country][state].setdefault(city, [])
        hierarchy[country][state][city].append(str(store.id))

    return hierarchy
