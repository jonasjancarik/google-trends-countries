"""Rank only complete measurements; keep uncertainty and denominator years visible."""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr

from country_attention.periods import StudyWindow

METRICS = [
    "relative_attention",
    "attention_per_million",
    "attention_residual",
    "adjusted_ratio",
    "total_attention_rank",
    "per_capita_rank",
    "adjusted_rank",
    "peak_month_share",
    "attention_without_peak",
    "per_capita_without_peak",
    "rank_without_peak",
    "foreign_attention_per_million",
    "absolute_searches",
]


def calculate_metrics(
    countries: pd.DataFrame, monthly: pd.DataFrame, window: StudyWindow
) -> pd.DataFrame:
    result = countries.copy()
    for name in METRICS:
        result[name] = np.nan
    result["observed_months"] = 0
    result["ranking_status"] = "Awaiting comparable search measurements"
    if monthly.empty:
        return result
    if monthly.duplicated(["iso3", "month"]).any():
        raise ValueError("Duplicate country-months")
    if not set(monthly.iso3).issubset(set(countries.iso3)):
        raise ValueError("Search measurements contain unknown countries")
    if not set(monthly.month).issubset(set(window.months)):
        raise ValueError("Measurements fall outside the study window")
    if (
        (monthly.relative_attention.dropna() <= 0)
        | ~np.isfinite(monthly.relative_attention.dropna())
    ).any():
        raise ValueError("Measured attention must be finite and positive")
    for iso3, group in monthly.groupby("iso3"):
        mask = result.iso3 == iso3
        result.loc[mask, "observed_months"] = group.relative_attention.notna().sum()
        if len(group) != 12 or group.relative_attention.isna().any():
            result.loc[mask, "ranking_status"] = "Incomplete or censored search measurements"
            continue
        if group.low_resolution.any():
            result.loc[mask, "ranking_status"] = (
                "Insufficient exported-score precision; ranking withheld"
            )
            continue
        attention = group.relative_attention.mean()
        peak = group.relative_attention.max()
        result.loc[mask, "relative_attention"] = attention
        result.loc[mask, "peak_month_share"] = peak / group.relative_attention.sum()
        result.loc[mask, "attention_without_peak"] = (group.relative_attention.sum() - peak) / 11
        population = result.loc[mask, "population"].iloc[0]
        if pd.isna(population) or population <= 0:
            result.loc[mask, "ranking_status"] = "Population unavailable"
        else:
            result.loc[mask, "ranking_status"] = "Eligible"
            result.loc[mask, "attention_per_million"] = attention / population * 1_000_000
            result.loc[mask, "per_capita_without_peak"] = (
                (group.relative_attention.sum() - peak) / 11 / population * 1_000_000
            )
    for field, rank in [
        ("relative_attention", "total_attention_rank"),
        ("attention_per_million", "per_capita_rank"),
        ("per_capita_without_peak", "rank_without_peak"),
    ]:
        result[rank] = result[field].rank(method="min", ascending=False)
    return result


def fit_attention_model(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """OLS log(attention) ~ log(population) + log(GDP), with HC3 standard errors."""
    frame = frame.copy()
    # Legacy callers may provide already matched observations. The pipeline always
    # supplies the independently selected common-year columns.
    separate = "model_year" in frame
    pop = "model_population" if separate else "population"
    gdp = "model_gdp_usd" if separate else "gdp_usd"
    year = frame.model_year if separate else frame.population_year
    complete = frame[["relative_attention", pop, gdp]].notna().all(axis=1)
    complete &= (frame[["relative_attention", pop, gdp]] > 0).all(axis=1)
    complete &= year.ge(frame.reference_year - 2) & year.le(frame.reference_year)
    if not separate:
        complete &= frame.population_year.eq(frame.gdp_usd_year)
    frame["model_status"] = "No positive population/GDP pair in the permitted years"
    frame.loc[frame.relative_attention.isna(), "model_status"] = "Search measurement not eligible"
    frame.loc[complete, "model_status"] = "Eligible"
    for field in [
        "attention_residual",
        "adjusted_ratio",
        "adjusted_rank",
        "model_log_fitted",
        "model_leverage",
        "model_cooks_distance",
    ]:
        frame[field] = np.nan
    valid = frame[complete.fillna(False)].copy()
    if len(valid) < 10:
        return frame, {
            "status": "unavailable",
            "reason": "At least 10 countries with complete attention and same-year population/GDP are required",
            "n": len(valid),
        }
    predictors = np.log(valid[[pop, gdp]].astype(float)).set_axis(["population", "gdp_usd"], axis=1)
    design = sm.add_constant(predictors)
    if np.linalg.matrix_rank(design) < 3:
        return frame, {
            "status": "unavailable",
            "reason": "Predictors are collinear",
            "n": len(valid),
        }
    fit = sm.OLS(np.log(valid.relative_attention.astype(float)), design).fit(cov_type="HC3")
    frame.loc[valid.index, "attention_residual"] = fit.resid
    frame.loc[valid.index, "adjusted_ratio"] = np.exp(fit.resid)
    frame["adjusted_rank"] = frame.attention_residual.rank(method="min", ascending=False)
    frame.loc[valid.index, "model_log_fitted"] = fit.fittedvalues
    frame.loc[valid.index, "model_leverage"] = fit.get_influence().hat_matrix_diag
    frame.loc[valid.index, "model_cooks_distance"] = fit.get_influence().cooks_distance[0]
    params = {k: float(v) for k, v in fit.params.items()}
    ci = {k: [float(v) for v in values] for k, values in fit.conf_int().T.items()}
    return frame, {
        "status": "available",
        "n": len(valid),
        "r_squared": float(fit.rsquared),
        "coefficients": params,
        "hc3_confidence_intervals_95": ci,
        "hc3_standard_errors": {k: float(v) for k, v in fit.bse.items()},
        "response_scale": "Natural logarithm of the annual relative attention index",
        "economic_selection": "Latest common positive World Bank population/GDP year within reference year minus two through reference year",
        "excluded": frame.loc[~complete, ["iso3", "model_status"]].to_dict("records")
        if "iso3" in frame
        else [],
        "condition_number": float(fit.condition_number),
        "note": "Exploratory association; interval estimates omit Google sampling/calibration uncertainty. Exp(fitted log attention) is a geometric prediction, not an arithmetic mean count.",
    }


def diagnostics(frame: pd.DataFrame) -> dict:
    ranked = frame[frame.per_capita_rank.notna()]
    result = {"ranked_countries": len(ranked), "relationships": {}}
    for field in ["population", "gdp_usd", "gdp_per_capita_usd", "tourist_arrivals"]:
        recent = frame[f"{field}_year"].ge(frame.reference_year - 2).fillna(False)
        subset = frame.loc[recent, ["relative_attention", field]].dropna()
        subset = subset[(subset > 0).all(axis=1)]
        if len(subset) >= 5 and subset.nunique().min() > 1:
            stat = spearmanr(subset.relative_attention, subset[field])
            result["relationships"][field] = {
                "spearman_rho": float(stat.statistic),
                "n": len(subset),
            }
        else:
            result["relationships"][field] = {
                "status": "unavailable",
                "reason": "At least five varying country pairs with recent indicator values are required",
                "n": len(subset),
            }
    small = ranked[["population", "attention_per_million"]].dropna()
    if len(small) >= 5 and small.nunique().min() > 1:
        result["population_vs_per_capita_rho"] = float(
            spearmanr(small.population, small.attention_per_million).statistic
        )
    adjusted = ranked[["per_capita_rank", "adjusted_rank"]].dropna()
    result["per_capita_vs_adjusted_rank_n"] = len(adjusted)
    if len(adjusted) >= 5 and adjusted.nunique().min() > 1:
        result["per_capita_vs_adjusted_rank_rho"] = float(
            spearmanr(adjusted.per_capita_rank, adjusted.adjusted_rank).statistic
        )
    return result


def foreign_per_capita(*, worldwide_counts, domestic_counts, population, unit: str):
    """Use only genuine compatible counts; regional Trends indices are never accepted."""
    if unit != "comparable_search_counts":
        raise ValueError(
            "Foreign attention requires comparable counts; regional indices cannot be subtracted"
        )
    total, domestic, pop = np.broadcast_arrays(
        np.asarray(worldwide_counts, dtype=float),
        np.asarray(domestic_counts, dtype=float),
        np.asarray(population, dtype=float),
    )
    if not (np.isfinite(total).all() and np.isfinite(domestic).all() and np.isfinite(pop).all()):
        raise ValueError("Counts and populations must be finite")
    if (domestic < 0).any() or (total < domestic).any() or (pop <= 0).any():
        raise ValueError("Invalid counts or population")
    return (total - domestic) / pop
