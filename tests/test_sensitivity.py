"""Known mathematical cases, separate from real research observations."""

import json

import numpy as np
import pandas as pd
import pytest
from test_measurements import WINDOW, batch, export_fixture

from country_attention.analysis import calculate_metrics, fit_attention_model
from country_attention.economics import model_economics
from country_attention.normalization import calibrate_batches, monthly_attention
from country_attention.panels import compare_panels
from country_attention.sensitivity import annual_precision, sensitivity_report
from country_attention.trends import import_google_csv


def test_latest_common_year_does_not_pair_different_years_or_use_old_data():
    history = pd.DataFrame(
        [
            ("A", "population", 2025, 120),
            ("A", "population", 2024, 110),
            ("A", "gdp_usd", 2024, 500),
            ("A", "gdp_usd", 2025, None),
            ("B", "population", 2022, 10),
            ("B", "gdp_usd", 2022, 100),
            ("C", "population", 2025, 20),
            ("C", "gdp_usd", 2025, 0),
            ("D", "population", 2026, 20),
            ("D", "gdp_usd", 2026, 100),
        ],
        columns=["iso3", "field", "year", "value"],
    )
    pairs = model_economics(history, 2025).set_index("iso3")
    assert pairs.index.tolist() == ["A"]
    assert pairs.loc["A"].to_dict() == {
        "model_year": 2024,
        "model_population": 110,
        "model_gdp_usd": 500,
    }
    with pytest.raises(ValueError, match="Duplicate"):
        model_economics(pd.concat([history, history.iloc[:1]]), 2025)


def test_model_uses_separate_denominators_and_leaves_per_capita_inputs_intact():
    rng = np.random.default_rng(2)
    pop = np.exp(rng.uniform(10, 20, 20))
    gdp = pop * np.exp(rng.uniform(5, 10, 20))
    frame = pd.DataFrame(
        {
            "iso3": [str(i) for i in range(20)],
            "population": pop * 1.2,
            "gdp_usd": gdp,
            "population_year": 2025,
            "gdp_usd_year": 2024,
            "model_population": pop,
            "model_gdp_usd": gdp,
            "model_year": 2024,
            "reference_year": 2025,
            "relative_attention": np.exp(
                0.5 * np.log(pop) + 0.2 * np.log(gdp) + rng.normal(0, 0.1, 20)
            ),
        }
    )
    result, report = fit_attention_model(frame)
    assert report["n"] == 20
    pd.testing.assert_series_equal(result.population, frame.population)
    assert result.adjusted_rank.notna().all()
    assert "logarithm" in report["response_scale"]
    result.model_year = 2026
    invalid, _ = fit_attention_model(result)
    assert invalid.adjusted_rank.isna().all()


def precision_fixture():
    raw = batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 20)])
    raw.loc[(raw.iso3 == "CZE") & raw.period_start.eq("2025-10-01"), "interest"] = 4
    scaled, _ = calibrate_batches(raw, anchor_iso3="FRA")
    return scaled


def test_annual_precision_weights_low_score_by_contribution_and_keeps_exclusion():
    scaled = precision_fixture()
    p = annual_precision(scaled, WINDOW, "FRA").set_index("iso3")
    assert p.loc["CZE", "low_score_intervals"] == 1
    assert p.loc["CZE", "low_score_annual_signal_share"] == pytest.approx(4 / (11 * 20 + 4))
    assert p.loc["CZE", "rounding_half_width_fraction"] == pytest.approx(0.5 / ((11 * 20 + 4) / 12))
    assert p.loc["FRA", "rounding_only_attention_lower"] == 100
    countries = pd.DataFrame({"iso3": ["FRA", "CZE"], "population": [1e6, 1e6]})
    metrics = calculate_metrics(countries, monthly_attention(scaled, WINDOW, "FRA"), WINDOW)
    assert pd.isna(metrics.set_index("iso3").loc["CZE", "per_capita_rank"])


def test_rounding_envelope_is_unavailable_for_censored_or_incomplete_year():
    scaled = precision_fixture()
    scaled.loc[scaled.iso3.eq("CZE") & scaled.period_start.eq("2025-10-01"), "interest"] = np.nan
    assert pd.isna(
        annual_precision(scaled, WINDOW, "FRA")
        .set_index("iso3")
        .loc["CZE", "rounding_only_attention_upper"]
    )
    incomplete = precision_fixture().drop(12)
    assert pd.isna(
        annual_precision(incomplete, WINDOW, "FRA")
        .set_index("iso3")
        .loc["CZE", "rounding_only_attention_lower"]
    )


def test_link_removal_disconnects_instead_of_claiming_stability():
    raw = pd.concat(
        [
            batch("a", [("FRA", "/m/fr", 100), ("CZE", "/m/cz", 20)]),
            batch("b", [("CZE", "/m/cz", 100), ("GEO", "/m/ge", 50)]),
            batch("c", [("CZE", "/m/cz", 100), ("TCD", "/m/td", 50)]),
        ]
    )
    scaled, info = calibrate_batches(raw, anchor_iso3="FRA")
    countries = pd.DataFrame({"iso3": ["FRA", "CZE", "GEO", "TCD"], "population": [1e6] * 4})
    rankings = calculate_metrics(countries, monthly_attention(scaled, WINDOW, "FRA"), WINDOW)
    rows, summary = sensitivity_report(raw, scaled, info, countries, rankings, WINDOW, "FRA")
    failed = next(s for s in summary["scenarios"] if s["name"] == "omit_CZE_from_calibration_links")
    assert failed["status"] == "unavailable"
    assert "Uncalibrated" in failed["reason"]
    assert (rows.scenario_rank_min == rows.primary_rank).all()
    assert (rows.rounding_only_best_rank <= rows.primary_rank).all()
    assert (rows.rounding_only_worst_rank >= rows.primary_rank).all()


def prepare_panel(root, value="20"):
    root.mkdir()
    csv, meta = export_fixture(root, raw_value=value)
    import_google_csv(csv, meta, root / "data/raw/trends")
    (root / "config").mkdir()
    (root / "config/study.json").write_text(
        json.dumps({"as_of": "2026-10-16", "anchor_iso3": "FRA"})
    )
    (root / "data/processed").mkdir()
    pd.DataFrame({"iso3": ["FRA", "CZE"], "population": [1e6, 1e6]}).to_csv(
        root / "data/processed/countries.csv", index=False
    )


def test_duplicate_panels_do_not_become_independent_samples(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    prepare_panel(first)
    prepare_panel(second)
    with pytest.raises(ValueError, match="not a new panel"):
        compare_panels(first, [second])


def test_panel_comparison_uses_common_eligible_cohort_and_fixed_populations(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    prepare_panel(first)
    prepare_panel(second, "4")
    # The repeat's own denominator is deliberately irrelevant.
    pd.DataFrame({"iso3": ["FRA", "CZE"], "population": [9e6, 9e6]}).to_csv(
        second / "data/processed/countries.csv", index=False
    )
    rows, summary = compare_panels(first, [second])
    rows = rows.set_index("iso3")
    assert summary["common_eligible_countries"] == 1
    assert rows.loc["FRA", "attention_per_million_repeat_1"] == pytest.approx(100)
    assert pd.isna(rows.loc["CZE", "observed_rank_min"])
    assert summary["excluded_from_comparison"] == ["CZE"]
    assert "not confidence intervals" in summary["interpretation"]
