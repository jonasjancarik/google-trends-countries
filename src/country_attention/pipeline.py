"""Reproducible assembly, data-quality receipts, and evidence-based reporting."""

import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from country_attention.acquisition import CachedHTTP
from country_attention.analysis import calculate_metrics, diagnostics, fit_attention_model
from country_attention.economics import apply_population_supplements, collect_economics
from country_attention.normalization import calibrate_batches, monthly_attention
from country_attention.periods import StudyWindow
from country_attention.trends import load_batches

MONTHLY_COLUMNS = [
    "iso3",
    "month",
    "days",
    "usable_days",
    "low_resolution_days",
    "monthly_approximation",
    "expected_days",
    "relative_attention",
    "low_resolution",
]


def save_text(path: Path, text: str):
    """Replace complete files atomically so a reader never sees a truncated CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def save_json(path: Path, data):
    save_text(path, json.dumps(data, indent=2, allow_nan=False) + "\n")


def build(
    root: Path,
    *,
    as_of: str,
    offline: bool = False,
    refresh: bool = False,
    anchor_iso3: str = "FRA",
    reference_year: int | None = None,
) -> dict:
    window = StudyWindow.trailing(as_of)
    reference_year = reference_year if reference_year is not None else int(window.end[:4]) - 1
    if reference_year >= int(as_of[:4]):
        raise ValueError("Use an economic reference year before the collection year")
    client = CachedHTTP(root / "data/raw/world_bank", offline=offline, refresh=refresh)
    countries, economic_history = collect_economics(client, reference_year)
    world_bank_population_available = int(countries.population.notna().sum())
    countries, population_supplements = apply_population_supplements(
        countries,
        root / "data/raw/population_supplements/reviewed-populations.json",
        reference_year=reference_year,
    )
    raw = load_batches(root / "data/raw/trends")
    monthly = pd.DataFrame(columns=MONTHLY_COLUMNS)
    calibration = {"status": "unavailable", "reason": "No audited topic exports have been imported"}
    if not raw.empty:
        calibrated, calibration = calibrate_batches(raw, anchor_iso3=anchor_iso3)
        monthly = monthly_attention(calibrated, window, anchor_iso3)
        calibration["status"] = "available"
    rankings = calculate_metrics(countries, monthly, window)
    rankings, model = fit_attention_model(rankings)
    analysis = diagnostics(rankings)
    out = root / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    save_text(out / "countries.csv", countries.to_csv(index=False))
    save_text(out / "economic_history.csv", economic_history.to_csv(index=False))
    save_text(out / "rankings.csv", rankings.to_csv(index=False))
    save_text(out / "monthly_attention.csv", monthly.to_csv(index=False))
    eligible = rankings[rankings.per_capita_rank.notna()]
    save_text(
        out / "top20.csv",
        eligible.sort_values(["per_capita_rank", "country"]).head(20).to_csv(index=False),
    )
    save_text(
        out / "bottom20.csv",
        eligible.sort_values(["attention_per_million", "country"]).head(20).to_csv(index=False),
    )
    save_json(out / "calibration.json", calibration)
    save_json(out / "regression.json", model)
    save_json(out / "diagnostics.json", analysis)
    probes = root / "data/raw/access_checks.json"
    provenance = {
        "generated_at": datetime.now(UTC).isoformat(),
        "as_of": as_of,
        "window_start": window.start,
        "window_end": window.end,
        "economic_reference_year": reference_year,
        "anchor_iso3": anchor_iso3,
        "universe_count": len(countries),
        "country_topics_with_exports": 0 if raw.empty else int(raw.iso3.nunique()),
        "google_export_count": int(raw.batch_id.nunique()) if not raw.empty else 0,
        "ranking_status_counts": {
            str(k): int(v) for k, v in rankings.ranking_status.value_counts().items()
        },
        "study_calendar_timezone": "Europe/Prague",
        "google_export_timezone": "Not specified in the date-only CSV; no sub-day conversion inferred",
        "un_members": int(countries.core_un_member.sum()),
        "population_available": int(countries.population.notna().sum()),
        "world_bank_population_available": world_bank_population_available,
        "population_supplements": population_supplements,
        "gdp_available": int(countries.gdp_usd.notna().sum()),
        "tourism_available": int(countries.tourist_arrivals.notna().sum()),
        "indicator_observation_years": {
            field: sorted(int(y) for y in countries[f"{field}_year"].dropna().unique())
            for field in ["population", "gdp_usd", "gdp_per_capita_usd", "tourist_arrivals"]
        },
        "ranked_countries": len(eligible),
        "measured_countries": int(rankings.relative_attention.notna().sum()),
        "attention_unit": "Relative mean search-share index; reference country mean = 100",
        "per_capita_unit": "Relative mean search-share index per million residents",
        "foreign_attention_status": "Unavailable: compatible origin search counts not obtained",
        "absolute_search_counts_status": "Unavailable: Google Trends does not provide absolute counts",
        "sources": client.receipts,
        "search_exports": [
            str(p.relative_to(root))
            for p in sorted((root / "data/raw/trends").glob("*/metadata.json"))
        ],
        "access_checks": json.loads(probes.read_text()) if probes.exists() else [],
        "browser_collection_status": json.loads(
            (root / "data/raw/browser_collection_status.json").read_text()
        )
        if (root / "data/raw/browser_collection_status.json").exists()
        else None,
        "notes": [
            "Annual country attention is an equal-month mean of relative search shares, not an annual count.",
            "Weekly observations are day-weighted approximations when split across calendar months.",
            "UN members and four additional entities are distinguished in all exports.",
            "GDP and population years are retained; regression requires same-year inputs within two years of the economic reference.",
            "Missing, censored and low-precision observations are never zero-filled for rankings.",
        ],
    }
    save_json(
        root / "config/study.json",
        {"as_of": as_of, "anchor_iso3": anchor_iso3, "reference_year": reference_year},
    )
    save_text(out / "report.md", make_report(rankings, provenance, model, analysis))
    # Written last, so its presence marks a completed snapshot.
    save_json(out / "provenance.json", provenance)
    return provenance


def make_report(rankings: pd.DataFrame, provenance: dict, model: dict, analysis: dict) -> str:
    p = provenance
    text = f"""# Country attention: preliminary results

Study period: {p["window_start"]} to {p["window_end"]}. Collection date: {p["as_of"]}.

## Available evidence

The dataset covers {p["un_members"]} UN member states and four separately identified entities:
the Holy See, Palestine, Taiwan and Kosovo. World Bank population data are available for
{p["world_bank_population_available"]} of {p["universe_count"]} entities, GDP for {p["gdp_available"]},
and tourist arrivals for {p["tourism_available"]}. Observation years accompany each value;
they need not match the search period. See `provenance.json` for exact requests and cache checksums.

Tourism observations in this snapshot refer to {", ".join(map(str, p["indicator_observation_years"]["tourist_arrivals"]))}.
They are historical context and cannot establish current tourism relationships.

Native browser exports cover {p["country_topics_with_exports"]} country topics in {p["google_export_count"]} comparisons.
These are original Google Trends measurements, not a third-party country-volume dataset.
The country-topic audit and original exports are documented in `docs/topic-audit.md` and `data/raw/trends/`.

"""
    if p["population_supplements"]:
        text += f"Reviewed official supplements bring population coverage to {p['population_available']} entities.\n\n"
        for record in p["population_supplements"]:
            text += (
                f"- {record['iso3']}: {record['population']:,} as of {record['population_as_of']}; "
                f"{record['population_definition']}. [Source]({record['population_source_url']}). "
                f"{record['population_note']}\n"
            )
        text += "\nThese denominators are not harmonized World Bank observations. Source, date and definition remain explicit in the country exports.\n\n"
    eligible = rankings[rankings.per_capita_rank.notna()].sort_values("per_capita_rank")
    if eligible.empty:
        text += """## Attention rankings are unavailable

No country currently meets the complete, uncensored, sufficient-precision and population criteria.
See each country's status and the source receipts for missing exports or measurements that fail
these requirements. `rankings.csv` preserves the full universe. Top/bottom exports contain no
ranked records, and no missing value is interpreted as zero searches.

"""
    else:
        text += f"## Attention rankings\n\n{len(eligible)} entities meet the complete, uncensored, sufficient-precision criteria.\n"
        text += f"This includes {int(eligible.core_un_member.sum())} UN members. "
        counts = p["ranking_status_counts"]
        text += (
            f"Exclusions comprise {counts.get('Low search-volume precision; ranking withheld', 0)} "
            f"low-precision series, {counts.get('Incomplete or censored search measurements', 0)} "
            f"incomplete or censored series, and {counts.get('Population unavailable', 0)} "
            "entities without population data.\n\n"
        )
        text += "Rankings apply only to that measured subset; missing countries may change the ordering.\n\n"
        text += "Very small populations can produce large per-capita values. Regression-adjusted rankings provide a separate comparison.\n\n"
        for label, subset in [
            ("Top 20", eligible.head(20)),
            ("Bottom 20", eligible.sort_values("attention_per_million").head(20)),
        ]:
            text += f"### {label} among measured countries\n\n| Country | Relative index per million residents |\n| --- | ---: |\n"
            for row in subset.itertuples():
                text += f"| {row.country} | {row.attention_per_million:.3g} |\n"
            text += "\n"
        if model["status"] == "available":
            text += f"The population-and-GDP log model uses {model['n']} countries (R² = {model['r_squared']:.3f}). "
            text += "It requires recent GDP and population observations from the same year, so its sample is smaller than the per-capita ranking. "
            text += "Residuals measure attention relative to a geometric prediction; they do not explain its causes.\n\n"
            adjusted = rankings[rankings.adjusted_rank.notna()].sort_values("adjusted_rank").head(5)
            text += "The largest positive adjusted residuals, expressed as multiples of the fitted prediction, are "
            text += (
                ", ".join(f"{r.country} ({r.adjusted_ratio:.2f})" for r in adjusted.itertuples())
                + ".\n\n"
            )
        else:
            text += f"Regression is unavailable: {model['reason']}.\n\n"
        if analysis.get("population_vs_per_capita_rho") is not None:
            text += f"The population/per-capita-attention Spearman correlation is {analysis['population_vs_per_capita_rho']:.3f}. "
            text += "The population denominator can create an inverse association mechanically.\n\n"
        if analysis.get("per_capita_vs_adjusted_rank_rho") is not None:
            text += f"Across the {analysis['per_capita_vs_adjusted_rank_n']} countries with both rankings, per-capita and regression-adjusted ranks have Spearman correlation {analysis['per_capita_vs_adjusted_rank_rho']:.3f}.\n\n"
        text += "Peak-month shares and ranks with each country's peak month removed are included for sensitivity analysis. A spike alone does not identify a news event.\n\n"
        peak_heavy = eligible.sort_values("peak_month_share", ascending=False).head(3)
        text += "The largest single-month contributions among eligible series are "
        text += (
            ", ".join(
                f"{r.country} ({r.peak_month_share:.1%} of its annual index sum)"
                for r in peak_heavy.itertuples()
            )
            + ". These are concentration measures, not evidence of a particular cause.\n\n"
        )
    text += """## Interpreting the index

Audited country topics can include related terms in multiple languages and reduce name
ambiguity. Shared topics connect comparison batches to one reference scale. The resulting
annual measure is the equal-month mean of relative search shares, with the reference country's
mean set to 100. Dividing by population gives an index per million residents. Neither measure
is a count of searches or unique people. Topic assignment, sampling, rounding and Google
coverage remain sources of uncertainty.

Foreign attention per capita is unavailable: regional Trends scores use different search
bases and cannot be subtracted from the worldwide index. The official API's consistent
scaling also does not establish additive regional counts. Google Ads estimates cover keyword
sets and close variants rather than the same country-topic construct; they are not mixed in.

## Remaining uncertainty

Low-precision and censored series remain excluded, so the bottom 20 are the lowest among
eligible countries, not established as the least-searched countries in the full universe.
Use weaker, linked references where they can improve integer precision. A series whose own
peak reaches 100 while its baseline is suppressed cannot be repaired simply by changing the
other country in the comparison. Weekly bucket splitting also makes the monthly and annual
indices approximations.

Repeated independent exports and alternative reference paths are needed to assess ranking
stability before publication. The model's HC3 intervals omit Google sampling and calibration
uncertainty. See `docs/methodology.md`, `docs/topic-audit.md` and `docs/research.md` for definitions,
territorial qualifications and source links.
"""
    return text
