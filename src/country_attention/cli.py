"""CLI entry points for collection, audited import and offline rebuilding."""

import argparse
from pathlib import Path

import pandas as pd

from country_attention.countries import country_universe
from country_attention.panels import compare_panels
from country_attention.periods import StudyWindow
from country_attention.pipeline import build, save_json, save_text
from country_attention.trends import import_google_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser(
        "build", help="Collect/cache economics, calibrate imports and write results"
    )
    run.add_argument("--as-of", default=str(pd.Timestamp.now(tz="Europe/Prague").date()))
    run.add_argument(
        "--offline", action="store_true", help="Fail rather than download uncached responses"
    )
    run.add_argument(
        "--refresh", action="store_true", help="Explicitly fetch new World Bank vintages"
    )
    run.add_argument(
        "--anchor", default="FRA", help="Audited reference topic ISO3, annual mean = 100"
    )
    run.add_argument("--reference-year", type=int)
    compare = sub.add_parser(
        "compare-panels", help="Compare separately collected panels using fixed populations"
    )
    compare.add_argument(
        "--panel",
        type=Path,
        action="append",
        required=True,
        help="Repeat project root containing data/raw/trends; repeat for each panel",
    )
    ingest = sub.add_parser("import-trends", help="Import an original CSV plus audited metadata")
    ingest.add_argument("--csv", type=Path, required=True)
    ingest.add_argument("--metadata", type=Path, required=True)
    sub.add_parser(
        "init-topics", help="Create an unverified topic-review worksheet; never overwrite"
    )
    sub.add_parser("window", help="Print the default trailing 12 complete months")
    args = parser.parse_args()
    try:
        if args.command == "build":
            if args.offline and args.refresh:
                parser.error("--offline and --refresh cannot be combined")
            result = build(
                args.root,
                as_of=args.as_of,
                offline=args.offline,
                refresh=args.refresh,
                anchor_iso3=args.anchor,
                reference_year=args.reference_year,
            )
            print(
                f"Saved {result['universe_count']} countries; {result['ranked_countries']} eligible for attention rankings."
            )
        elif args.command == "compare-panels":
            rows, report = compare_panels(args.root, args.panel)
            save_text(args.root / "data/processed/panel_comparison.csv", rows.to_csv(index=False))
            save_json(args.root / "data/processed/panel_comparison.json", report)
            print(
                f"Compared {len(report['panels'])} panels on {report['common_eligible_countries']} common eligible countries; these are observed ranges, not confidence intervals."
            )
        elif args.command == "import-trends":
            print(import_google_csv(args.csv, args.metadata, args.root / "data/raw/trends"))
        elif args.command == "init-topics":
            frame = country_universe()[["iso3", "country", "membership"]]
            for field in [
                "topic_id",
                "topic_label",
                "verification_note",
                "source_url",
                "reviewed_at",
            ]:
                frame[field] = ""
            frame["verified_country_topic"] = False
            path = args.root / "config/topic_registry.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x") as handle:
                frame.to_csv(handle, index=False)
            print(path)
        else:
            window = StudyWindow.trailing()
            print(f"{window.start} to {window.end}")
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        parser.exit(1, f"Cannot complete {args.command}: {exc}\n")


if __name__ == "__main__":
    main()
