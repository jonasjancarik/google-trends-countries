"""Calibrate comparison batches through shared topics on identical intervals.

This estimates relative search *shares*, never counts. It is a transparent
anchor-graph estimator inspired by G-TAB, not an implementation of its anchor bank.
"""

from itertools import combinations

import numpy as np
import pandas as pd

from country_attention.periods import StudyWindow


class CalibrationError(ValueError):
    pass


def calibrate_batches(
    raw: pd.DataFrame,
    *,
    anchor_iso3: str,
    min_overlap: int = 6,
    min_interest: float = 5,
    tolerance: float = 0.2,
) -> tuple[pd.DataFrame, dict]:
    required = {
        "batch_id",
        "iso3",
        "topic_id",
        "period_start",
        "period_end",
        "interest",
        "censored",
        "resolution",
        "geo",
        "category",
        "property",
        "window_start",
        "window_end",
        "timezone",
    }
    if not required.issubset(raw.columns) or raw.empty:
        raise CalibrationError("No valid comparison observations")
    for field in [
        "geo",
        "category",
        "property",
        "resolution",
        "window_start",
        "window_end",
        "timezone",
    ]:
        if raw[field].nunique(dropna=False) != 1:
            raise CalibrationError(f"All comparisons must share {field}")
    if raw.geo.iloc[0] != "" or raw.category.iloc[0] != 0 or raw.property.iloc[0] != "":
        raise CalibrationError("Only worldwide all-category Web Search can be calibrated")
    if (raw.groupby("iso3").topic_id.nunique() > 1).any():
        raise CalibrationError("Country topic identities changed between batches")
    if (raw.groupby("topic_id").iso3.nunique() > 1).any():
        raise CalibrationError("A topic is assigned to more than one country")
    keys = ["batch_id", "topic_id", "period_start", "period_end"]
    if raw.duplicated(keys).any():
        raise CalibrationError("Duplicate observations within a batch")
    values = pd.to_numeric(raw.interest, errors="raise")
    if ((values.notna()) & (~np.isfinite(values) | (values <= 0) | (values > 100))).any():
        raise CalibrationError("Uncensored interest must be finite and within (0, 100]")
    if not raw.censored.isin([True, False]).all() or not (raw.censored == values.isna()).all():
        raise CalibrationError("Censoring flags do not match missing/low-volume observations")
    batches = sorted(raw.batch_id.unique())
    roots = sorted(
        raw.loc[(raw.iso3 == anchor_iso3) & raw.interest.ge(min_interest), "batch_id"].unique()
    )
    if not roots:
        raise CalibrationError("The reference country has no usable observations")
    root = roots[0]
    edges, neighbors = [], {b: set() for b in batches}
    for a, b in combinations(batches, 2):
        matched = raw[raw.batch_id == a].merge(
            raw[raw.batch_id == b],
            on=["topic_id", "period_start", "period_end"],
            suffixes=("_a", "_b"),
            validate="one_to_one",
        )
        usable = matched[matched.interest_a.ge(min_interest) & matched.interest_b.ge(min_interest)]
        if len(usable) < min_overlap:
            continue
        logs = np.log(usable.interest_a.to_numpy() / usable.interest_b.to_numpy())
        logratio = float(np.median(logs))
        spread = float(np.quantile(np.abs(logs - logratio), 0.9))
        if spread > tolerance:
            raise CalibrationError(f"Unstable shared-topic ratio between {a} and {b}: {spread:.3f}")
        edges.append(
            {
                "a": a,
                "b": b,
                "log_ratio": logratio,
                "overlap": len(usable),
                "p90_log_deviation": spread,
            }
        )
        neighbors[a].add(b)
        neighbors[b].add(a)
    connected, todo = {root}, [root]
    while todo:
        for b in neighbors[todo.pop()] - connected:
            connected.add(b)
            todo.append(b)
    if connected != set(batches):
        raise CalibrationError(f"Uncalibrated batches: {sorted(set(batches) - connected)}")
    variables = [b for b in batches if b != root]
    scales = {root: 1.0}
    max_residual = 0.0
    if variables:
        matrix, target = [], []
        for edge in edges:
            weight = np.sqrt(edge["overlap"])
            matrix.append([weight * ((b == edge["b"]) - (b == edge["a"])) for b in variables])
            target.append(weight * edge["log_ratio"])
        coefficients = np.linalg.lstsq(np.asarray(matrix), np.asarray(target), rcond=None)[0]
        scales.update(
            {b: float(np.exp(coef)) for b, coef in zip(variables, coefficients, strict=True)}
        )
        for edge in edges:
            residual = abs(np.log(scales[edge["b"]] / scales[edge["a"]]) - edge["log_ratio"])
            max_residual = max(max_residual, float(residual))
        if max_residual > tolerance:
            raise CalibrationError(
                "Inconsistent calibration cycles; collect better overlapping anchors"
            )
    scaled = raw.copy()
    scaled["scale_factor"] = scaled.batch_id.map(scales)
    scaled["relative_interest"] = scaled.interest * scaled.scale_factor
    # Repeated reference topics are measurements of the same series, not additive traffic.
    # Prefer the export with the finest original integer precision for each interval.
    scaled = scaled.sort_values(
        ["interest", "batch_id"], ascending=[False, True], na_position="last"
    )
    scaled = scaled.drop_duplicates(["iso3", "period_start", "period_end"], keep="first")
    return scaled, {
        "root_batch": root,
        "anchor_iso3": anchor_iso3,
        "scales": scales,
        "edges": edges,
        "max_cycle_log_residual": max_residual,
        "min_overlap": min_overlap,
        "min_interest": min_interest,
        "tolerance": tolerance,
    }


def monthly_attention(scaled: pd.DataFrame, window: StudyWindow, anchor_iso3: str) -> pd.DataFrame:
    """Day-weight interval means into months; incomplete/censored months stay missing."""
    pieces = []
    for _, group in scaled.groupby("iso3"):
        ordered = group.sort_values("period_start")
        starts = pd.to_datetime(ordered.period_start)
        ends = pd.to_datetime(ordered.period_end)
        if starts.isna().any() or ends.isna().any() or (ends < starts).any():
            raise CalibrationError("Invalid source interval dates")
        if (starts.iloc[1:].to_numpy() <= ends.iloc[:-1].to_numpy()).any():
            raise CalibrationError("Overlapping source intervals for one country")
    for row in scaled.itertuples():
        start = max(pd.Timestamp(row.period_start), pd.Timestamp(window.start))
        end = min(pd.Timestamp(row.period_end), pd.Timestamp(window.end))
        if start > end:
            continue
        for month in pd.period_range(start, end, freq="M"):
            left, right = max(start, month.start_time), min(end, month.end_time.normalize())
            days = (right - left).days + 1
            pieces.append(
                {
                    "iso3": row.iso3,
                    "month": str(month),
                    "days": days,
                    "usable_days": 0 if pd.isna(row.relative_interest) else days,
                    "weighted": 0.0
                    if pd.isna(row.relative_interest)
                    else row.relative_interest * days,
                    "low_resolution_days": days
                    if pd.notna(row.interest) and row.interest < 5
                    else 0,
                    "monthly_approximation": row.resolution == "weekly",
                }
            )
    if not pieces:
        raise CalibrationError("No observations fall within the study window")
    frame = (
        pd.DataFrame(pieces)
        .groupby(["iso3", "month"], as_index=False)
        .agg(
            days=("days", "sum"),
            usable_days=("usable_days", "sum"),
            weighted=("weighted", "sum"),
            low_resolution_days=("low_resolution_days", "sum"),
            monthly_approximation=("monthly_approximation", "max"),
        )
    )
    frame["expected_days"] = pd.PeriodIndex(frame.month, freq="M").days_in_month
    if (frame.days > frame.expected_days).any():
        raise CalibrationError(
            "Source intervals overlap; monthly observations would be double-counted"
        )
    complete = (frame.usable_days == frame.expected_days) & (frame.days == frame.expected_days)
    frame["relative_attention"] = (frame.weighted / frame.expected_days).where(complete)
    anchor = frame[(frame.iso3 == anchor_iso3) & frame.relative_attention.notna()]
    if set(anchor.month) != set(window.months) or anchor.relative_attention.mean() <= 0:
        raise CalibrationError("Reference topic needs 12 complete, uncensored months")
    denominator = float(anchor.relative_attention.mean())
    frame["relative_attention"] = 100 * frame.relative_attention / denominator
    frame["low_resolution"] = frame.low_resolution_days.gt(0)
    return frame.drop(columns="weighted")
