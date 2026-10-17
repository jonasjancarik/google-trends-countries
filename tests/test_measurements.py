"""Synthetic mathematical fixtures only; never shipped as research observations."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from country_attention.acquisition import CachedHTTP, world_bank_pages
from country_attention.analysis import calculate_metrics, fit_attention_model, foreign_per_capita
from country_attention.countries import country_universe, resolve_country
from country_attention.normalization import CalibrationError, calibrate_batches, monthly_attention
from country_attention.periods import StudyWindow
from country_attention.trends import import_google_csv, load_batches

WINDOW = StudyWindow("2025-10-01", "2026-09-30")


def batch(name, values):
    rows = []
    for iso3, topic, level in values:
        for month in WINDOW.months:
            period = pd.Period(month, freq="M")
            rows.append(
                {
                    "batch_id": name,
                    "iso3": iso3,
                    "topic_id": topic,
                    "period_start": str(period.start_time.date()),
                    "period_end": str(period.end_time.date()),
                    "interest": level,
                    "censored": pd.isna(level),
                    "resolution": "monthly",
                    "geo": "",
                    "category": 0,
                    "property": "",
                    "window_start": WINDOW.start,
                    "window_end": WINDOW.end,
                    "timezone": "UTC",
                }
            )
    return pd.DataFrame(rows)


def test_universe_and_name_resolution():
    countries = country_universe()
    assert len(countries) == 197
    assert countries.core_un_member.sum() == 193
    assert countries.iso3.nunique() == 197
    for name, code in [
        ("Turkey", "TUR"),
        ("Türkiye", "TUR"),
        ("Côte d'Ivoire", "CIV"),
        ("CZ", "CZE"),
        ("Kosovo", "XKX"),
        ("DR Congo", "COD"),
        ("Georgia", "GEO"),
        ("Chad", "TCD"),
        ("Jordan", "JOR"),
    ]:
        assert resolve_country(name) == code
    for name in ["Congo", "Korea", "Atlantis", "Gergia"]:
        with pytest.raises(ValueError):
            resolve_country(name)


def test_complete_calendar_window():
    assert StudyWindow.trailing("2026-10-16") == WINDOW
    assert StudyWindow.trailing("2024-03-01").end == "2024-02-29"
    with pytest.raises(ValueError):
        StudyWindow("2025-10-02", "2026-09-30")


def test_chained_calibration_recovers_known_ratios_without_adding_duplicates():
    raw = pd.concat(
        [
            batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 20)]),
            batch("b", [("CZE", "/m/cz", 100), ("GEO", "/m/ge", 50)]),
            batch("c", [("GEO", "/m/ge", 100), ("TCD", "/m/td", 50)]),
        ]
    )
    scaled, info = calibrate_batches(raw, anchor_iso3="FRA")
    assert info["scales"]["b"] == pytest.approx(0.2)
    assert info["scales"]["c"] == pytest.approx(0.1)
    monthly = monthly_attention(scaled, WINDOW, "FRA")
    assert len(monthly) == 48
    means = monthly.groupby("iso3").relative_attention.mean()
    assert means.to_dict() == pytest.approx({"FRA": 100, "CZE": 20, "GEO": 10, "TCD": 5})
    # Arbitrary global scaling disappears under the reference-country convention.
    scaled.relative_interest *= 17
    pd.testing.assert_series_equal(
        monthly.relative_attention, monthly_attention(scaled, WINDOW, "FRA").relative_attention
    )


def test_disconnected_or_low_precision_anchors_are_rejected():
    raw = pd.concat(
        [
            batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 1)]),
            batch("b", [("CZE", "/m/cz", 100), ("GEO", "/m/ge", 50)]),
        ]
    )
    with pytest.raises(CalibrationError, match="Uncalibrated"):
        calibrate_batches(raw, anchor_iso3="FRA")


@pytest.mark.parametrize(
    "field,value",
    [("geo", "US"), ("category", 7), ("window_start", "2020-01-01"), ("resolution", "weekly")],
)
def test_incompatible_comparisons_rejected(field, value):
    raw = batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 20)])
    raw.loc[raw.iso3 == "CZE", field] = value
    with pytest.raises(CalibrationError):
        calibrate_batches(raw, anchor_iso3="FRA")


def test_unstable_anchor_ratios_rejected():
    a = batch("a", [("FRA", "/m/fr", 100)])
    b = batch("b", [("FRA", "/m/fr", 50)])
    b.loc[b.index[:6], "interest"] = 10
    with pytest.raises(CalibrationError, match="Unstable"):
        calibrate_batches(pd.concat([a, b]), anchor_iso3="FRA")


def test_censored_month_is_not_zero_or_ranked():
    raw = batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 20)])
    raw.loc[12, ["interest", "censored"]] = [np.nan, True]
    scaled, _ = calibrate_batches(raw, anchor_iso3="FRA")
    monthly = monthly_attention(scaled, WINDOW, "FRA")
    assert monthly[monthly.iso3 == "CZE"].relative_attention.isna().sum() == 1
    countries = pd.DataFrame({"iso3": ["FRA", "CZE"], "population": [10_000_000, 1_000_000]})
    metrics = calculate_metrics(countries, monthly, WINDOW).set_index("iso3")
    assert pd.isna(metrics.loc["CZE", "per_capita_rank"])
    assert metrics.loc["FRA", "attention_per_million"] == 10


def test_per_capita_and_missing_denominator():
    monthly = monthly_attention(*_scaled_args())
    countries = pd.DataFrame(
        {"iso3": ["FRA", "CZE", "GEO"], "population": [10_000_000, 1_000_000, np.nan]}
    )
    metrics = calculate_metrics(countries, monthly, WINDOW).set_index("iso3")
    assert metrics.loc["CZE", "attention_per_million"] == pytest.approx(20)
    assert metrics.loc["CZE", "per_capita_rank"] == 1
    assert pd.isna(metrics.loc["GEO", "attention_per_million"])
    assert metrics.absolute_searches.isna().all()
    assert metrics.foreign_attention_per_million.isna().all()


def _scaled_args():
    raw = batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 20), ("GEO", "/m/ge", 10)])
    scaled, _ = calibrate_batches(raw, anchor_iso3="FRA")
    return scaled, WINDOW, "FRA"


def test_day_weighted_weekly_month_boundary():
    scaled, window, anchor = _scaled_args()
    # Replace France January with intervals of different lengths to test day weights.
    scaled = scaled[~((scaled.iso3 == "FRA") & scaled.period_start.eq("2026-01-01"))]
    base = scaled.iloc[0].to_dict()
    pieces = []
    for start, end, value in [("2026-01-01", "2026-01-07", 70), ("2026-01-08", "2026-01-31", 100)]:
        pieces.append(
            {
                **base,
                "iso3": "FRA",
                "period_start": start,
                "period_end": end,
                "relative_interest": value,
                "resolution": "weekly",
            }
        )
    scaled = pd.concat([scaled, pd.DataFrame(pieces)], ignore_index=True)
    monthly = monthly_attention(scaled, window, anchor)
    january = (70 * 7 + 100 * 24) / 31
    reference_mean = (100 * 11 + january) / 12
    observed = monthly[(monthly.iso3 == "FRA") & monthly.month.eq("2026-01")].iloc[0]
    assert observed.relative_attention == pytest.approx(100 * january / reference_mean)
    assert observed.monthly_approximation


def test_foreign_requires_compatible_counts():
    assert (
        foreign_per_capita(
            worldwide_counts=100, domestic_counts=20, population=10, unit="comparable_search_counts"
        )
        == 8
    )
    for unit in ["regional_index", "relative_attention"]:
        with pytest.raises(ValueError, match="cannot be subtracted"):
            foreign_per_capita(worldwide_counts=100, domestic_counts=20, population=10, unit=unit)
    with pytest.raises(ValueError):
        foreign_per_capita(
            worldwide_counts=10, domestic_counts=20, population=10, unit="comparable_search_counts"
        )


def test_log_model_residuals_and_global_scale_invariance():
    rng = np.random.default_rng(8)
    n = 30
    population = np.exp(rng.uniform(10, 20, n))
    gdp = population * np.exp(rng.uniform(6, 11, n))
    attention = np.exp(2 + 0.25 * np.log(population) + 0.1 * np.log(gdp) + rng.normal(0, 0.3, n))
    frame = pd.DataFrame(
        {
            "relative_attention": attention,
            "population": population,
            "gdp_usd": gdp,
            "population_year": 2025,
            "gdp_usd_year": 2025,
            "reference_year": 2025,
            "attention_residual": np.nan,
            "adjusted_ratio": np.nan,
        }
    )
    first, report = fit_attention_model(frame)
    frame.relative_attention *= 100
    second, _ = fit_attention_model(frame)
    assert report["status"] == "available"
    assert report["n"] == 30
    np.testing.assert_allclose(first.attention_residual, second.attention_residual, atol=1e-10)
    np.testing.assert_allclose(first.adjusted_ratio, np.exp(first.attention_residual))
    frame.gdp_usd_year = 2024
    _, report = fit_attention_model(frame)
    assert report["status"] == "unavailable"


def export_fixture(tmp_path: Path, *, raw_value="20", verified=True):
    csv = tmp_path / "export.csv"
    csv.write_text(
        "Category: All categories\n\nMonth,France: (Worldwide),Czechia: (Worldwide)\n"
        + "".join(f"{month},100,{raw_value}\n" for month in WINDOW.months)
    )
    metadata = {
        "batch_id": "test-fixture",
        "geo": "",
        "category": 0,
        "property": "",
        "window_start": WINDOW.start,
        "window_end": WINDOW.end,
        "resolution": "monthly",
        "timezone": "UTC",
        "source_url": "https://trends.google.com/trends/explore",
        "retrieved_at": "2026-10-16T10:00:00Z",
        "topic_columns": {
            "France: (Worldwide)": {
                "iso3": "FRA",
                "topic_id": "/m/test-fr",
                "verified_country_topic": verified,
                "verification_note": "Synthetic test fixture",
            },
            "Czechia: (Worldwide)": {
                "iso3": "CZE",
                "topic_id": "/m/test-cz",
                "verified_country_topic": verified,
                "verification_note": "Synthetic test fixture",
            },
        },
    }
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata))
    return csv, path


def test_csv_import_preserves_censoring_and_rejects_overwrite(tmp_path):
    csv, metadata = export_fixture(tmp_path, raw_value="<1")
    destination = import_google_csv(csv, metadata, tmp_path / "raw")
    loaded = load_batches(tmp_path / "raw")
    assert len(loaded) == 24
    assert loaded[loaded.iso3 == "CZE"].interest.isna().all()
    assert loaded[loaded.iso3 == "CZE"].censored.all()
    assert (destination / "google-export.csv").read_bytes() == csv.read_bytes()
    with pytest.raises(FileExistsError):
        import_google_csv(csv, metadata, tmp_path / "raw")


def test_csv_import_requires_reviewed_topics(tmp_path):
    csv, metadata = export_fixture(tmp_path, verified=False)
    with pytest.raises(ValueError, match="reviewed"):
        import_google_csv(csv, metadata, tmp_path / "raw")


def test_world_bank_pagination_and_errors():
    class Pages:
        def get_json(self, url, params):
            return [{"page": params["page"], "pages": 2}, [{"value": params["page"]}]]

    assert world_bank_pages(Pages(), "country") == [{"value": 1}, {"value": 2}]

    class Failure:
        def get_json(self, url, params):
            return [{"message": [{"value": "Invalid value"}]}]

    with pytest.raises(ValueError, match="Unexpected"):
        world_bank_pages(Failure(), "country")


def test_offline_missing_cache_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        CachedHTTP(tmp_path, offline=True).get_json("https://api.worldbank.org/v2/country")


def test_import_integrity_detects_modified_parsed_data(tmp_path):
    csv, metadata = export_fixture(tmp_path)
    destination = import_google_csv(csv, metadata, tmp_path / "raw")
    path = destination / "observations.csv"
    path.write_text(path.read_text().replace(",20.0,", ",90.0,"))
    with pytest.raises(ValueError, match="checksum"):
        load_batches(tmp_path / "raw")


def test_low_precision_country_is_withheld_even_with_complete_months():
    raw = batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 4)])
    scaled, _ = calibrate_batches(raw, anchor_iso3="FRA")
    monthly = monthly_attention(scaled, WINDOW, "FRA")
    metrics = calculate_metrics(
        pd.DataFrame({"iso3": ["FRA", "CZE"], "population": [1e6, 1e6]}), monthly, WINDOW
    ).set_index("iso3")
    assert metrics.loc["CZE", "observed_months"] == 12
    assert pd.isna(metrics.loc["CZE", "per_capita_rank"])
    assert "precision" in metrics.loc["CZE", "ranking_status"]


def test_overlapping_intervals_rejected_even_if_coverage_sum_could_hide_gap():
    scaled, window, anchor = _scaled_args()
    row = scaled.iloc[0].to_dict()
    duplicate = {**row, "period_start": "2025-10-10", "period_end": "2025-10-20"}
    with pytest.raises(CalibrationError, match="Overlapping"):
        monthly_attention(pd.concat([scaled, pd.DataFrame([duplicate])]), window, anchor)
