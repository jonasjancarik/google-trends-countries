"""Import measured Google Trends CSVs; no scraping or fabricated topic IDs."""

import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from country_attention.countries import country_universe, resolve_country

REQUIRED_META = {
    "batch_id",
    "geo",
    "category",
    "property",
    "window_start",
    "window_end",
    "resolution",
    "source_url",
    "retrieved_at",
    "topic_columns",
    "timezone",
}


def import_google_csv(csv_path: Path, metadata_path: Path, output: Path) -> Path:
    """Preserve the original export, metadata and parsed observations in a batch directory."""
    meta = json.loads(metadata_path.read_text())
    missing = REQUIRED_META - meta.keys()
    if missing:
        raise ValueError(f"Missing export metadata: {sorted(missing)}")
    if meta["geo"] != "" or meta["category"] != 0 or meta["property"] != "":
        raise ValueError("Only worldwide, all-category, Google Web Search comparisons are accepted")
    if meta["resolution"] not in {"monthly", "weekly", "daily"}:
        raise ValueError("Resolution must be monthly, weekly or daily")
    ZoneInfo(meta["timezone"])
    if urlparse(meta["source_url"]).hostname != "trends.google.com":
        raise ValueError("Record the original trends.google.com comparison URL")
    datetime.fromisoformat(meta["retrieved_at"].replace("Z", "+00:00"))
    start, end = pd.Timestamp(meta["window_start"]), pd.Timestamp(meta["window_end"])
    if start > end:
        raise ValueError("Invalid source window")
    if pd.Timestamp(meta["retrieved_at"]).tz_localize(None).normalize() <= end:
        raise ValueError("Import only completed source windows")
    universe = set(country_universe().iso3)
    topic_ids = set()
    iso_codes = set()
    for column, topic in meta["topic_columns"].items():
        if topic.get("verified_country_topic") is not True or not topic.get("verification_note"):
            raise ValueError(f"Country topic must be explicitly reviewed: {column}")
        topic_id = topic.get("topic_id", "")
        if not topic_id.startswith(("/m/", "/g/")):
            raise ValueError("Use entity topic IDs, never plain search terms")
        if topic["iso3"] not in universe or resolve_country(topic["iso3"]) != topic["iso3"]:
            raise ValueError("Unknown country code in topic manifest")
        if topic_id in topic_ids or topic["iso3"] in iso_codes:
            raise ValueError("Each country/topic can occur only once in a comparison")
        topic_ids.add(topic_id)
        iso_codes.add(topic["iso3"])
    if not 1 <= len(topic_ids) <= 8:
        raise ValueError("A comparison must contain 1 to 8 audited topics")
    text = csv_path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    header = next(
        (i for i, line in enumerate(lines) if line.startswith(("Month,", "Week,", "Day,"))), None
    )
    if header is None:
        raise ValueError("Expected an English Google Trends Month, Week or Day CSV header")
    frame = pd.read_csv(io.StringIO("\n".join(lines[header:])), dtype=str, keep_default_na=False)
    date_column = frame.columns[0]
    expected = {"monthly": "Month", "weekly": "Week", "daily": "Day"}[meta["resolution"]]
    if date_column != expected or set(frame.columns[1:]) != set(meta["topic_columns"]):
        raise ValueError("CSV columns/resolution do not match the audited topic manifest")
    if frame.empty or frame[date_column].duplicated().any():
        raise ValueError("Export is empty or has duplicate periods")
    rows = []
    for item in frame.to_dict("records"):
        period = pd.Timestamp(item[date_column])
        if meta["resolution"] == "monthly":
            if period.day != 1:
                raise ValueError("Monthly observations must start on day 1")
            interval_end = period + pd.offsets.MonthEnd(0)
        else:
            interval_end = period + pd.Timedelta(days=6 if meta["resolution"] == "weekly" else 0)
        interval_start, interval_end = max(period, start), min(interval_end, end)
        if interval_start > interval_end:
            raise ValueError("Observation falls outside the recorded request window")
        for column, topic in meta["topic_columns"].items():
            raw = item[column].strip()
            if raw in {"", "<1", "< 1", "0"}:
                value = np.nan  # Zero is censored, not evidence of no searches.
                censored = True
            else:
                try:
                    value = float(raw)
                except ValueError:
                    raise ValueError(f"Invalid Google interest value: {raw!r}") from None
                if not np.isfinite(value) or not 0 < value <= 100:
                    raise ValueError(f"Interest must be within 0-100: {raw}")
                censored = False
            rows.append(
                {
                    "batch_id": meta["batch_id"],
                    "iso3": topic["iso3"],
                    "topic_id": topic["topic_id"],
                    "period_start": str(interval_start.date()),
                    "period_end": str(interval_end.date()),
                    "interest": value,
                    "censored": censored,
                    "resolution": meta["resolution"],
                    "geo": "",
                    "category": 0,
                    "property": "",
                    "window_start": meta["window_start"],
                    "window_end": meta["window_end"],
                    "timezone": meta["timezone"],
                }
            )
    parsed = pd.DataFrame(rows)
    for _, group in parsed.groupby("iso3"):
        ordered = group.sort_values("period_start")
        if (
            pd.to_datetime(ordered.period_start).iloc[1:].to_numpy()
            <= pd.to_datetime(ordered.period_end).iloc[:-1].to_numpy()
        ).any():
            raise ValueError("Overlapping source intervals")
    # No overwrite: each export has an immutable, auditable origin.
    batch = str(meta["batch_id"])
    if not batch or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in batch
    ):
        raise ValueError("Batch ID must use letters, digits, hyphens or underscores")
    destination = output / batch
    destination.mkdir(parents=True, exist_ok=False)
    source = csv_path.read_bytes()
    (destination / "google-export.csv").write_bytes(source)
    (destination / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    parsed.to_csv(destination / "observations.csv", index=False)
    (destination / "receipt.json").write_text(
        json.dumps(
            {
                "sha256": hashlib.sha256(source).hexdigest(),
                "source_url": meta["source_url"],
                "retrieved_at": meta["retrieved_at"],
                "row_count": len(parsed),
                "observations_sha256": hashlib.sha256(
                    (destination / "observations.csv").read_bytes()
                ).hexdigest(),
                "metadata_sha256": hashlib.sha256(
                    (destination / "metadata.json").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    return destination


def load_batches(root: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(root.glob("*/observations.csv")):
        directory = path.parent
        receipt = json.loads((directory / "receipt.json").read_text())
        if (
            hashlib.sha256((directory / "google-export.csv").read_bytes()).hexdigest()
            != receipt["sha256"]
        ):
            raise ValueError(f"Raw export checksum mismatch: {directory}")
        for filename, key in [
            ("observations.csv", "observations_sha256"),
            ("metadata.json", "metadata_sha256"),
        ]:
            if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != receipt[key]:
                raise ValueError(f"Imported batch checksum mismatch: {directory / filename}")
        frames.append(pd.read_csv(path, keep_default_na=False, na_values={"interest": [""]}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
