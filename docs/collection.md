# Collecting and rebuilding the study

Read this before importing search data or refreshing source vintages.

## Rebuild the delivered snapshot

From the project directory:

```bash
uv sync --locked
uv run country-attention build --as-of 2026-10-16 --reference-year 2025 --offline
pnpm --dir web install
pnpm --dir web dev
```

Offline mode requires the supplied World Bank cache and fails if any request is absent or its checksum differs. It makes no Google requests. A normal `build` reuses existing cache entries; use `--refresh` deliberately to download a new World Bank vintage. Advancing `--as-of` changes the study window and may require new economics cache entries and new search exports. Use a copy of the project to preserve an earlier processed snapshot; raw content-addressed World Bank response bodies remain available after refresh.

The CLI accepts `--root /absolute/project/path` **before** the command. An economic reference year can be fixed explicitly. All processed products are regenerated from the raw cache and audited imports. The supplied output contains real country-topic indices and rankings for the subset meeting the precision and population rules.

## Review topics

`config/topic_registry.csv` contains the 197-entity review worksheet, initially unverified. `init-topics` creates it for a fresh project and refuses to overwrite it. Record the country topic ID, label, verification source/date and notes. This worksheet is an audit aid; each imported batch's manifest is the authoritative binding to CSV columns.

In Google Trends, choose the actual country **topic**, not the search term. Check the entity type and related searches, especially ambiguous names. Select Worldwide, all categories and Web Search. Keep a record of the full comparison URL. A Wikidata Freebase ID or autocomplete result is only a candidate until its Google meaning has been reviewed. Never mark a topic verified to get past validation without reviewing it.

## Export linked comparisons

1. Fix one source window and resolution for every comparison. Use the study window, 1 October 2025–30 September 2026, for this snapshot. The interface commonly returns weekly values for a year. Monthly exports are supported when available; do not relabel weekly data as monthly.
2. Begin with the reviewed France country topic as the default reference and several other country topics. Download the **Interest over time** CSV in English. Do not use the Interest by region export.
3. Include shared topics in later comparisons. For countries too small beside France, compare them beside a weaker country already measured, adding bridge comparisons as needed. Calibration needs a connected graph and at least six shared topic/interval values of 5 or more per link. Several independent links improve diagnostics. The importer allows up to eight topics, subject to the actual UI limit.
4. Keep every query setting and source interval identical. Wait between manual requests. If Google returns a rate-limit response, stop and use its normal access/retry guidance; the project does not automate or evade Google limits. Cache each export and reuse it.
5. Obtain repeated independent exports and alternative anchor paths for a publication study. Use separate project copies for repeated full panels: the current estimator is a single-panel calibration and does not produce sampling confidence intervals.

If alpha API access is granted, its consistently scaled series may remove the need for UI calibration. A tested API adapter is not included because the public reviewed documentation does not expose a usable endpoint contract for unapproved clients. Do not pass API series through the UI importer as if they were 0–100 exports. Implement a separate adapter with verified units and scale scope first.

## Import an original CSV

Copy `config/batch-metadata.example.json` outside the raw data directory and edit it. Use a unique batch ID. Set `topic_columns` keys to the **exact** CSV headers. Each column must bind to its country ISO3 and reviewed `/m/...` or `/g/...` entity identifier, with `verified_country_topic: true` and a concrete `verification_note`. The template deliberately contains placeholders and an unverified flag, so it cannot silently become a real observation.

Record the actual retrieval time, original comparison URL, source date window, returned resolution and common study-calendar interpretation (Europe/Prague here). Google's date-only CSV does not identify its source time zone. Keep browser/date settings consistent and do not infer sub-day timestamps. See docs/topic-audit.md. Then run:

```bash
uv run country-attention import-trends --csv /path/to/original.csv --metadata /path/to/reviewed-metadata.json
uv run country-attention build --as-of 2026-10-16 --reference-year 2025 --anchor FRA --offline
```

The importer preserves the original bytes, manifest, receipt and parsed observations in `data/raw/trends/<batch_id>/`, refusing to overwrite an existing batch. Suppressed values remain censored. Import rejects search terms, unreviewed entities, non-worldwide origins, mismatched columns, overlapping periods, invalid scores and incomplete source windows still in progress. Parsing accepts English Month/Week/Day exports, including the usual preamble. A partial source window is clipped only where recorded; incomplete study months cannot enter rankings.

Calibration failures stop the build and leave the prior results in place. Read the error and resolve topic identity, date alignment, precision or missing links; do not remove the gate to force a ranking. After a successful rebuild, restart `pnpm --dir web dev` or run `pnpm --dir web build` so the web page picks up the new outputs; both copy `data/processed/` into `web/public/data/` when they start.

## Output files

- `countries.csv`: full country universe and observed economic denominators, with years.
- `economic_history.csv`: all retrieved indicator observations, including missing values.
- `rankings.csv`: full universe, measurement status, total relative index, index per million, adjusted ranks and event-sensitivity fields.
- `monthly_attention.csv`: comparable country-month indices and coverage/precision flags.
- `top20.csv`, `bottom20.csv`: eligible countries only; headers with zero records when unavailable.
- `calibration.json`, `regression.json`, `diagnostics.json`: fitted scales and analysis status/results.
- `provenance.json`: exact requests, cache checksums, retrieval times, definitions and access-check outcomes.
- `report.md`: generated analytical findings or explicit measurement limitations.

The web page's table download follows its membership, region and country-name filters and contains the original `rankings.csv` columns. The page also links the complete `rankings.csv` and `monthly_attention.csv`. It fetches no external data source, and no refresh is scheduled automatically.

## Browser collection completed for this snapshot

The normal browser interface supplied original weekly exports for all 197 entities after the direct HTTP probe had returned 429. The selected country identity and all comparison settings were reviewed in the UI. Historical Freebase mappings were used only to discover candidate identifiers; films, a US state, an island and other mismatches were rejected. See `docs/topic-audit.md`.

The common references include France, Czechia, Canada, Fiji and Nauru. Here, weaker means lower measured search interest. Follow-up references were selected from measured peak magnitudes to improve integer precision; population was never used to estimate missing attention. `config/browser-batches/` records all 76 successful imports. `config/browser-refinement-plan.json` preserves the completed refinement plan, and `config/refinement-decisions.csv` records its outcomes. The first resumed collection added 65 eligible entities, bringing the per-capita ranking to 192. Subsequent official population supplements added Taiwan and the Holy See/Vatican City row, bringing it to 194. Cabo Verde, Comoros and Haiti still fail the precision rule despite reaching 100 in their own series.

After full entity coverage and some refinement, Google showed “Oops! There was a problem displaying this page. Please try again.” The same page still failed after one normal reload, and further requests stopped. A later normal visit succeeded. All 17 pending batches and two final paired comparisons were then imported and passed the full calibration checks. No HTTP status was exposed by the UI for the earlier error, so it is not recorded as a confirmed HTTP 429. See `data/raw/browser_collection_status.json` and the historical access checks. No automatic refresh or delayed collection is scheduled.

The latest precision retry is recorded in `data/raw/followup_checks/2026-10-16/receipt.json`. Cabo Verde's new paired export is imported as `browser-075`; Haiti and Comoros repeats are byte-identical to earlier exports and are retained outside the calibration input. No independent-sample stability conclusion follows from identical downloads.

## Official population supplements

The supplied snapshot includes `data/raw/population_supplements/reviewed-populations.json` and the two original official HTML responses. The normal offline build loads this manifest, verifies each source-body checksum and fills only missing World Bank populations. No network request is made for supplements during a build. It fails if a reviewed record is outside the selected economic reference window; changing the reference year may therefore require a newly reviewed population source. The manifest is a curated source binding, not an automatic population scraper.

Country exports retain source, exact observation date, definition and qualifications for each population. World Bank history remains in `economic_history.csv`; the two official records and receipts remain separately identified in provenance. See [the methodology](methodology.md#economic-denominators-and-model) for the Taiwan registration and Vatican City residency qualifications.
