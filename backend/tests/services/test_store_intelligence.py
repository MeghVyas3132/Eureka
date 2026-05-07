from types import SimpleNamespace

from services.store_intelligence import StoreIntelligenceEngine, build_store_hierarchy


def test_parse_store_name_extracts_chain_city_state_pin_and_confidence():
    parsed = StoreIntelligenceEngine().parse("RF Indiranagar BLR 560038")

    assert parsed["detected_chain"] == "Reliance Fresh"
    assert parsed["city"] == "Bangalore"
    assert parsed["state"] == "Karnataka"
    assert parsed["pin_code"] == "560038"
    assert parsed["parse_confidence"] >= 0.8


def test_build_store_hierarchy_groups_by_country_state_city():
    stores = [
        SimpleNamespace(id="s1", country="India", state="Karnataka", city="Bangalore"),
        SimpleNamespace(id="s2", country="India", state="Karnataka", city="Bangalore"),
        SimpleNamespace(id="s3", country="India", state=None, city=None),
    ]

    hierarchy = build_store_hierarchy(stores)

    assert hierarchy["India"]["Karnataka"]["Bangalore"] == ["s1", "s2"]
    assert hierarchy["India"]["Unknown State"]["Unknown City"] == ["s3"]
