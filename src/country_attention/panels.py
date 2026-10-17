"""Compare separately archived panels without claiming that exports are independent."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from country_attention.analysis import calculate_metrics
from country_attention.normalization import calibrate_batches, monthly_attention
from country_attention.periods import StudyWindow
from country_attention.trends import load_batches


def compare_panels(root: Path, panel_roots: list[Path]) -> tuple[pd.DataFrame, dict]:
    """Panel roots contain data/raw/trends; use one fixed denominator set for all panels."""
    settings = json.loads((root / "config/study.json").read_text())
    window = StudyWindow.trailing(settings["as_of"])
    anchor = settings["anchor_iso3"]
    countries = pd.read_csv(root / "data/processed/countries.csv")
    originals = load_batches(root / "data/raw/trends")
    fields = ["geo", "category", "property", "resolution", "window_start", "window_end"]
    signature = originals[fields].drop_duplicates().to_dict("records")
    identities = (
        originals[["iso3", "topic_id"]].drop_duplicates().sort_values("iso3").reset_index(drop=True)
    )
    results, panels, seen_hashes = {}, [], set()
    for number, path in enumerate([root, *panel_roots]):
        name = "primary" if number == 0 else f"repeat_{number}"
        raw = load_batches(path / "data/raw/trends")
        if raw.empty or raw[fields].drop_duplicates().to_dict("records") != signature:
            raise ValueError(f"{name}: panel settings differ from the primary panel")
        topics = (
            raw[["iso3", "topic_id"]].drop_duplicates().sort_values("iso3").reset_index(drop=True)
        )
        if not topics.equals(identities):
            raise ValueError(f"{name}: collect the same complete country-topic universe")
        receipts = [
            json.loads(p.read_text())
            for p in sorted((path / "data/raw/trends").glob("*/receipt.json"))
        ]
        hashes = {r["sha256"] for r in receipts}
        if number and hashes <= seen_hashes:
            raise ValueError(
                f"{name}: all exports already occur in earlier panels; this is not a new panel"
            )
        shared = len(hashes & seen_hashes)
        seen_hashes.update(hashes)
        scaled, _ = calibrate_batches(raw, anchor_iso3=anchor)
        metrics = calculate_metrics(
            countries, monthly_attention(scaled, window, anchor), window
        ).set_index("iso3")
        results[name] = metrics.attention_per_million
        panels.append(
            {
                "name": name,
                "exports": len(receipts),
                "shared_export_hashes": shared,
                "export_sha256": sorted(hashes),
                "retrieved_at_first": min(r["retrieved_at"] for r in receipts),
                "retrieved_at_last": max(r["retrieved_at"] for r in receipts),
                "eligible_countries": int(metrics.per_capita_rank.notna().sum()),
            }
        )
    if len(results) < 2:
        raise ValueError("Supply at least one separately collected panel")
    values = pd.DataFrame(results)
    common = values.dropna()
    if common.empty:
        raise ValueError("No common eligible countries across panels")
    ranks = common.rank(ascending=False, method="min")
    output = values.rename(columns=lambda name: f"attention_per_million_{name}")
    for name in ranks:
        output[f"rank_{name}_common_cohort"] = ranks[name]
    output["observed_rank_min"] = ranks.min(axis=1)
    output["observed_rank_max"] = ranks.max(axis=1)
    output["eligible_in_all_panels"] = output.index.isin(common.index)
    comparisons = []
    cutoff = min(20, len(common))
    for name in list(results)[1:]:
        shift = ranks[name] - ranks["primary"]
        percent = 100 * (common[name] / common["primary"] - 1)
        comparisons.append(
            {
                "panel": name,
                "changed_ranks": int(shift.ne(0).sum()),
                "maximum_absolute_rank_change": float(shift.abs().max()),
                "median_absolute_score_change_percent": float(percent.abs().median()),
                "maximum_absolute_score_change_percent": float(percent.abs().max()),
                "top_rank_cutoff": cutoff,
                "top_group_overlap": int(
                    (ranks[name].le(cutoff) & ranks["primary"].le(cutoff)).sum()
                ),
            }
        )
    summary = {
        "panels": panels,
        "comparisons_to_primary": comparisons,
        "primary_countries_sha256": hashlib.sha256(
            (root / "data/processed/countries.csv").read_bytes()
        ).hexdigest(),
        "common_eligible_countries": len(common),
        "excluded_from_comparison": sorted(set(values.index) - set(common.index)),
        "interpretation": "Observed repeat-panel ranges, not confidence intervals. Distinct hashes or collection dates do not establish independent Google samples. Shared exports are explicitly counted.",
        "denominators": "Primary panel populations held fixed in all comparisons",
        "window_start": window.start,
        "window_end": window.end,
    }
    return output.rename_axis("iso3").reset_index(), summary
