"""World Bank indicators and reviewed official population supplements."""

import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from country_attention.acquisition import CachedHTTP, world_bank_pages
from country_attention.countries import country_universe

INDICATORS = {
    "population": "SP.POP.TOTL",
    "gdp_usd": "NY.GDP.MKTP.CD",
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
    "tourist_arrivals": "ST.INT.ARVL",
}


def collect_economics(client: CachedHTTP, reference_year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    countries = country_universe()
    metadata = world_bank_pages(client, "country")
    # Join only known alpha-3 identities, never aggregate regions from country/all.
    meta = pd.DataFrame(
        [
            {
                "iso3": x["id"],
                "region": x["region"]["value"],
                "income_group": x["incomeLevel"]["value"],
                "world_bank_name": x["name"],
            }
            for x in metadata
            if x["region"]["id"] != "NA"
        ]
    )
    countries = countries.merge(meta, on="iso3", how="left", validate="one_to_one")
    countries["region"] = countries.region.fillna("Not covered by World Bank")
    history = []
    for field, indicator in INDICATORS.items():
        data = world_bank_pages(
            client,
            f"country/all/indicator/{indicator}",
            date=f"{reference_year - 5}:{reference_year}",
            source=2,
        )
        for x in data:
            iso3 = x.get("countryiso3code")
            if iso3 not in set(countries.iso3):
                continue
            history.append(
                {
                    "iso3": iso3,
                    "indicator": indicator,
                    "field": field,
                    "year": int(x["date"]),
                    "value": x["value"],
                    "unit": x.get("unit", ""),
                    "obs_status": x.get("obs_status", ""),
                }
            )
    history = pd.DataFrame(history)
    for field in INDICATORS:
        valid = history[(history.field == field) & history.value.notna() & (history.value > 0)]
        latest = valid.sort_values("year").drop_duplicates("iso3", keep="last")
        latest = latest[["iso3", "value", "year"]].rename(
            columns={"value": field, "year": f"{field}_year"}
        )
        countries = countries.merge(latest, on="iso3", how="left", validate="one_to_one")
        countries[f"{field}_year"] = countries[f"{field}_year"].astype("Int64")
    countries["reference_year"] = reference_year
    return countries, history


def apply_population_supplements(
    countries: pd.DataFrame, manifest: Path, *, reference_year: int
) -> tuple[pd.DataFrame, list[dict]]:
    """Fill absent populations from audited official records; never replace a WB value."""
    result = countries.copy()
    result["population_source"] = "World Bank"
    result["population_source_url"] = "https://data.worldbank.org/indicator/SP.POP.TOTL"
    result["population_as_of"] = ""
    result["population_definition"] = "World Bank total population (SP.POP.TOTL)"
    result["population_note"] = "Observation year retained; no projection to the search period."
    result.loc[
        result.population.isna(),
        ["population_source", "population_source_url", "population_definition", "population_note"],
    ] = ""
    if not manifest.exists():
        return result, []
    records = json.loads(manifest.read_text())["records"]
    seen = set()
    for record in records:
        iso = record["iso3"]
        mask = result.iso3.eq(iso)
        value, year = record["population"], record["population_year"]
        if iso in seen or mask.sum() != 1 or not record.get("verified_official_population"):
            raise ValueError("Duplicate, unknown or unreviewed population supplement")
        seen.add(iso)
        if result.loc[mask, "population"].notna().any():
            raise ValueError(f"Population supplement would replace World Bank data: {iso}")
        if isinstance(value, bool) or not math.isfinite(value) or value <= 0 or value != int(value):
            raise ValueError(f"Invalid population supplement: {iso}")
        if not reference_year - 5 <= year <= reference_year:
            raise ValueError(f"Population supplement outside economic reference window: {iso}")
        observed_at = pd.Timestamp(record["population_as_of"])
        if observed_at.year != year or not record["population_source_url"].startswith("https://"):
            raise ValueError(f"Invalid population supplement date or source: {iso}")
        body = manifest.parent / record["body_file"]
        if body.resolve().parent != manifest.parent.resolve():
            raise ValueError("Population source must remain inside its cache directory")
        if hashlib.sha256(body.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"Population source checksum mismatch: {iso}")
        for field in [
            "population",
            "population_year",
            "population_source",
            "population_source_url",
            "population_as_of",
            "population_definition",
            "population_note",
        ]:
            result.loc[mask, field] = record[field]
    return result, records


def model_economics(history: pd.DataFrame, reference_year: int) -> pd.DataFrame:
    """Latest common recent year, separate from the per-capita denominator vintage."""
    eligible = history[
        history.field.isin(["population", "gdp_usd"])
        & history.year.between(reference_year - 2, reference_year)
        & history.value.gt(0)
    ]
    if eligible.duplicated(["iso3", "year", "field"]).any():
        raise ValueError("Duplicate economic observations for model selection")
    paired = eligible.pivot(index=["iso3", "year"], columns="field", values="value")
    paired = paired.reindex(columns=["population", "gdp_usd"]).dropna().reset_index()
    paired = paired.sort_values("year").drop_duplicates("iso3", keep="last")
    return paired.rename(
        columns={"year": "model_year", "population": "model_population", "gdp_usd": "model_gdp_usd"}
    ).rename_axis(columns=None)
