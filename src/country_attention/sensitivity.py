"""Deterministic sensitivity checks; these do not estimate Google sampling error."""

import numpy as np
import pandas as pd

from country_attention.analysis import calculate_metrics
from country_attention.normalization import CalibrationError, calibrate_batches, monthly_attention
from country_attention.periods import StudyWindow


def annual_precision(scaled: pd.DataFrame, window: StudyWindow, anchor: str) -> pd.DataFrame:
    """Rounding-only envelopes conditional on fixed fitted scales and interval allocation.

    Each observed integer y represents [max(0, y-.5), min(100, y+.5)].
    Sampling, suppression, calibration, population and topic error are not covered.
    Censored or incomplete years have no envelope. Excluded countries get diagnostics,
    never a primary rank or an imputed primary annual index.
    """
    rows = []
    for iso, group in scaled.groupby("iso3"):
        total = lower = upper = low_signal = 0.0
        covered = 0
        censored = False
        for r in group.itertuples():
            start = max(pd.Timestamp(r.period_start), pd.Timestamp(window.start))
            end = min(pd.Timestamp(r.period_end), pd.Timestamp(window.end))
            if start > end:
                continue
            covered += (end - start).days + 1
            if pd.isna(r.interest):
                censored = True
                continue
            weight = 0.0
            for month in pd.period_range(start, end, freq="M"):
                days = (
                    min(end, month.end_time.normalize()) - max(start, month.start_time)
                ).days + 1
                weight += days / month.days_in_month / 12
            total += weight * r.relative_interest
            lower += weight * max(0, r.interest - 0.5) * r.scale_factor
            upper += weight * min(100, r.interest + 0.5) * r.scale_factor
            if r.interest < 5:
                low_signal += weight * r.relative_interest
        complete = covered == (pd.Timestamp(window.end) - pd.Timestamp(window.start)).days + 1
        usable = complete and not censored and total > 0
        rows.append(
            {
                "iso3": iso,
                "source_intervals": len(group),
                "low_score_intervals": int(group.interest.lt(5).sum()),
                "low_score_annual_signal_share": low_signal / total if usable else np.nan,
                "rounding_lower_unscaled": lower if usable else np.nan,
                "rounding_upper_unscaled": upper if usable else np.nan,
                "rounding_half_width_fraction": (upper - lower) / (2 * total) if usable else np.nan,
            }
        )
    frame = pd.DataFrame(rows)
    ref = frame.set_index("iso3").loc[anchor]
    frame["rounding_only_attention_lower"] = (
        100 * frame.rounding_lower_unscaled / ref.rounding_upper_unscaled
    )
    frame["rounding_only_attention_upper"] = (
        100 * frame.rounding_upper_unscaled / ref.rounding_lower_unscaled
    )
    frame.loc[
        frame.iso3.eq(anchor), ["rounding_only_attention_lower", "rounding_only_attention_upper"]
    ] = 100.0
    return frame


def sensitivity_report(
    raw: pd.DataFrame,
    scaled: pd.DataFrame,
    calibration: dict,
    countries: pd.DataFrame,
    rankings: pd.DataFrame,
    window: StudyWindow,
    anchor: str,
) -> tuple[pd.DataFrame, dict]:
    baseline = rankings.set_index("iso3")
    eligible = baseline.index[baseline.per_capita_rank.notna()]
    ranks = {"primary": baseline.loc[eligible, "per_capita_rank"]}
    scenarios = []

    def record(name, observations):
        monthly = monthly_attention(observations, window, anchor)
        metrics = calculate_metrics(countries, monthly, window).set_index("iso3")
        if metrics.reindex(eligible).attention_per_million.isna().any():
            raise CalibrationError("Scenario loses a primary eligible country's measurement")
        # Hold the comparison cohort fixed; eligibility changes must not look like movement.
        candidate = metrics.loc[eligible, "attention_per_million"].rank(
            ascending=False, method="min"
        )
        ranks[name] = candidate
        delta = candidate - ranks["primary"]
        scenarios.append(
            {
                "name": name,
                "status": "available",
                "countries": len(eligible),
                "changed_ranks": int(delta.ne(0).sum()),
                "max_absolute_rank_shift": float(delta.abs().max()) if len(delta) else 0.0,
            }
        )

    all_scaled = raw.copy()
    all_scaled["scale_factor"] = all_scaled.batch_id.map(calibration["scales"])
    all_scaled["relative_interest"] = all_scaled.interest * all_scaled.scale_factor
    keys = ["iso3", "period_start", "period_end"]
    median = all_scaled[all_scaled.interest.ge(5)].groupby(keys).relative_interest.median()
    alternative = scaled.set_index(keys).copy()
    alternative["relative_interest"] = median.reindex(alternative.index).fillna(
        alternative.relative_interest
    )
    record("median_high_precision_measurements", alternative.reset_index())

    # Give each accepted link equal weight rather than counting correlated weeks as precision.
    root = calibration["root_batch"]
    variables = sorted(set(raw.batch_id) - {root})
    edges = calibration["edges"]
    if variables:
        design = np.array([[int(b == e["b"]) - int(b == e["a"]) for b in variables] for e in edges])
        coef = np.linalg.lstsq(design, np.array([e["log_ratio"] for e in edges]), rcond=None)[0]
        scales = {root: 1.0, **dict(zip(variables, np.exp(coef), strict=True))}
        residual = max(abs(np.log(scales[e["b"]] / scales[e["a"]]) - e["log_ratio"]) for e in edges)
        if residual <= calibration["tolerance"]:
            alternative = scaled.copy()
            alternative["scale_factor"] = alternative.batch_id.map(scales)
            alternative["relative_interest"] = alternative.interest * alternative.scale_factor
            record("equal_weight_calibration_links", alternative)
        else:
            scenarios.append(
                {
                    "name": "equal_weight_calibration_links",
                    "status": "unavailable",
                    "reason": "Fitted link residual exceeds the primary tolerance",
                }
            )

    # Remove each widely reused bridge topic from link estimation, retaining its observations.
    # This changes calibration information; changing the final reference alone does not.
    shared = raw.groupby("iso3").batch_id.nunique()
    link_topics = {t for e in edges for t in e["topics"]}
    for topic in sorted(shared.index[(shared >= 3) & shared.index.isin(link_topics)]):
        name = f"omit_{topic}_from_calibration_links"
        try:
            alternative, _ = calibrate_batches(
                raw, anchor_iso3=anchor, exclude_link_topics=frozenset({topic})
            )
            record(name, alternative)
        except CalibrationError as exc:
            scenarios.append({"name": name, "status": "unavailable", "reason": str(exc)})

    frame = annual_precision(scaled, window, anchor).set_index("iso3")
    rank_frame = pd.DataFrame(ranks)
    frame["primary_rank"] = baseline.per_capita_rank
    frame["scenario_rank_min"] = rank_frame.min(axis=1)
    frame["scenario_rank_max"] = rank_frame.max(axis=1)
    frame["scenario_count"] = rank_frame.count(axis=1).reindex(frame.index).fillna(0).astype(int)
    for name in rank_frame:
        frame[f"rank_{name}"] = rank_frame[name]
    # Rank envelopes use unnormalized annual levels: the shared France denominator cancels.
    lower = frame.loc[eligible, "rounding_lower_unscaled"] / baseline.loc[eligible, "population"]
    upper = frame.loc[eligible, "rounding_upper_unscaled"] / baseline.loc[eligible, "population"]
    for iso in eligible:
        others = eligible[eligible != iso]
        frame.loc[iso, "rounding_only_best_rank"] = 1 + int(lower.loc[others].gt(upper[iso]).sum())
        frame.loc[iso, "rounding_only_worst_rank"] = 1 + int(upper.loc[others].gt(lower[iso]).sum())
    frame = frame.drop(columns=["rounding_lower_unscaled", "rounding_upper_unscaled"])
    ordered = baseline.loc[eligible, "attention_per_million"].sort_values()
    summary = {
        "status": "available",
        "cohort": "Primary eligible entities, including additional entities",
        "eligible_countries": len(eligible),
        "adjacent_pairs_within_one_percent": int(ordered.pct_change().lt(0.01).sum()),
        "scenarios": scenarios,
        "sampling_uncertainty": "Not estimated: one collection panel; scenario ranges are not confidence intervals",
        "rounding_scope": "Conditional on fitted scales, chosen observations, fixed populations and constant within-interval shares; excludes sampling, privacy noise and calibration error",
        "eligibility_policy": "Unchanged: twelve complete months, no censored intervals and every selected score at least 5",
        "annual_precision_policy": "Diagnostic only; no annual uncertainty threshold has been empirically validated",
    }
    return frame.reset_index(), summary
