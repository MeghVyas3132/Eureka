from ingestion.sku_deduplicator import SKUDeduplicator, normalise_for_dedup


def test_normalise_for_dedup_removes_stopwords_and_normalises_units():
    key = normalise_for_dedup("Coca Cola 500 ML Bottle")
    assert key == "500ml coca cola"


def test_find_duplicates_flags_intra_and_cross_import_matches():
    deduplicator = SKUDeduplicator()

    incoming_rows = [
        {"sku": "COKE-001", "name": "Coke 500 ML"},
        {"sku": "COKE-002", "name": "Coca Cola 500ml"},
    ]
    existing_products = [
        {"sku": "COKE-X", "name": "Coca Cola 500 ml"},
    ]

    flags = deduplicator.find_duplicates(incoming_rows, existing_products)

    assert len(flags) == 2
    assert {flag["source"] for flag in flags} == {"cross_import", "intra_file"}
    assert flags[0]["similarity"] >= deduplicator.SIMILARITY_THRESHOLD
