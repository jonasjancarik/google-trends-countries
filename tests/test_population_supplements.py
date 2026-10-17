"""Guard source integrity, observation dates and missing-only population supplementation."""

import hashlib
import json

import pandas as pd
import pytest

from country_attention.economics import apply_population_supplements


def fixture(tmp_path):
    body = b"Reviewed official population source fixture"
    (tmp_path / "source.html").write_bytes(body)
    record = {
        "iso3": "TWN",
        "population": 100,
        "population_year": 2025,
        "population_as_of": "2025-12-31",
        "population_source": "Official fixture",
        "population_source_url": "https://example.org/population",
        "population_definition": "Registered population at year end",
        "population_note": "Synthetic test; never used as a research observation.",
        "body_file": "source.html",
        "sha256": hashlib.sha256(body).hexdigest(),
        "verified_official_population": True,
    }
    manifest = tmp_path / "reviewed-populations.json"
    manifest.write_text(json.dumps({"records": [record]}))
    countries = pd.DataFrame(
        {
            "iso3": ["TWN", "CZE"],
            "population": [float("nan"), 200],
            "population_year": pd.array([None, 2025], dtype="Int64"),
        }
    )
    return countries, manifest, record


def test_reviewed_supplement_preserves_world_bank_and_provenance(tmp_path):
    countries, manifest, _ = fixture(tmp_path)
    result, receipts = apply_population_supplements(countries, manifest, reference_year=2025)
    assert countries.population.isna().iloc[0]
    assert result.population.tolist() == [100, 200]
    assert result.population_source.tolist() == ["Official fixture", "World Bank"]
    assert result.population_as_of.iloc[0] == "2025-12-31"
    assert receipts[0]["population_definition"] == "Registered population at year end"


@pytest.mark.parametrize("problem", ["checksum", "overwrite", "future", "duplicate", "unreviewed"])
def test_invalid_population_supplements_fail_closed(tmp_path, problem):
    countries, manifest, record = fixture(tmp_path)
    records = [record]
    if problem == "checksum":
        (tmp_path / "source.html").write_text("Changed after review")
    elif problem == "overwrite":
        countries.loc[0, "population"] = 50
    elif problem == "future":
        record.update(population_year=2026, population_as_of="2026-12-31")
    elif problem == "duplicate":
        records.append(record.copy())
    else:
        record["verified_official_population"] = False
    manifest.write_text(json.dumps({"records": records}))
    with pytest.raises(ValueError):
        apply_population_supplements(countries, manifest, reference_year=2025)
