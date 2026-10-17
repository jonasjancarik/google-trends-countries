# Country attention

A Python research pipeline and interactive web page for asking which countries receive disproportionate worldwide Google search attention relative to population.

**Current status:** Original country-topic CSV exports cover all **197 entities**, including every UN member. **194 entities**—**190 UN members** and all four additional entities—have per-capita ranks. Lower-interest reference comparisons recovered 65 measurement exclusions; reviewed official population supplements subsequently added Taiwan and the Holy See/Vatican City row. Cabo Verde, Comoros and Haiti still fail the unchanged minimum-score rule after paired retries. All **76 comparison exports** pass calibration. Identical repeat downloads are preserved as access checks rather than additional calibration batches. Scores are relative search-share indices, not search counts.

## Run

Requires Python 3.13 or 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run country-attention build --as-of 2026-10-16 --reference-year 2025 --offline
```

The supplied World Bank cache and original Google exports make this snapshot reproducible without network access after dependency installation. To collect a new study window, omit `--offline`; existing requests remain cached. Use `--refresh` only when a new World Bank vintage is intended. See the [collection guide](docs/collection.md) for auditing topics and importing original Google Trends CSVs.

The presentation page in `web/` is a React and Vite app. It requires Node.js and [pnpm](https://pnpm.io/), and reads the files in `data/processed/` directly, so rebuild the dataset first:

```bash
cd web
pnpm install
pnpm dev
```

Open [localhost:5173](http://localhost:5173). `pnpm build` writes a static site to `web/dist/` that any file host can serve. Both commands first copy the current processed outputs and map geometry into `web/public/data/`; that copy is generated and not tracked.

## Deploy

The page is published on Cloudflare Pages at [country-attention.pages.dev](https://country-attention.pages.dev) (project `country-attention`, production branch `main`). The [CI workflow](.github/workflows/ci.yml) runs the Python tests, ruff and the web build on every push and pull request; pushes to `main` then deploy the built page. Deploys need a `CLOUDFLARE_API_TOKEN` repository secret with Cloudflare Pages edit permission and a `CLOUDFLARE_ACCOUNT_ID` repository variable. Without them, the deploy step is skipped with a warning.

To deploy by hand, build and upload with Wrangler through `npx`. The `cf` CLI created the project, but it cannot upload Pages files yet:

```bash
pnpm --dir web build
npx wrangler@4 pages deploy web/dist --project-name country-attention --branch main
```

Set `CLOUDFLARE_ACCOUNT_ID` when your Cloudflare login can reach more than one account.

## Data

The study window is **October 2025–September 2026**, the last twelve complete months before 16 October 2026. The dataset contains all **193 UN members**, plus the Holy See, Palestine, Taiwan and Kosovo, identified separately. World Bank population observations cover **195/197** entities, GDP **191/197**, and optional tourism **120/197**. Reviewed official supplements bring population coverage to **197/197**: Taiwan's year-end registered population and Vatican City's year-end residents. Their sources, exact dates, definitions and qualifications remain in the exports; these are not harmonized World Bank observations. Every indicator retains its observation year. Tourism values are from 2020 and are historical context only; correlations exclude them. Kosovo's XK/XKX identifiers are a user-assigned convention, not official ISO assignments.

[`data/processed/rankings.csv`](data/processed/rankings.csv) includes all countries, published indices, ranks and explicit exclusion reasons. Top/bottom-20 exports contain the eligible subset; countries failing the measurement rules are not assigned a zero or a rank. [`data/processed/report.md`](data/processed/report.md) describes the supported findings and the evidence still needed.

The web page presents the per-resident map, top and bottom rankings, the population and GDP relationship, the countries furthest above and below the population-and-GDP prediction, monthly comparisons and a searchable table with CSV export. It defaults to the 193 UN members, with a switch to add the four other entities; displayed ranks are counted within the countries shown. Small states missing from the 110m map outline appear as circles at approximate coordinates. Countries that fail the measurement rules stay visible as unranked rather than being given a low score, and the page explains why foreign attention cannot be separated out. Regression diagnostics, calibration details and request provenance remain in the files under `data/processed/`.

## Measurement

Country topics are reviewed individually to reduce language and name ambiguity. Shared topic/interval observations connect comparison exports into a common scale. Calibration rejects mismatched settings, disconnected batches and unstable ratios; rankings require twelve complete months without censored or low-precision intervals. The reference country's annual mean is set to 100. Chaining comparisons through weaker country topics can help preserve precision for small countries.

Here, a weaker reference means a topic with lower measured search interest. A comparison dominated by France can round a small country's weekly scores to zero or very small integers. Lower-interest references such as Fiji or Nauru let those countries use more of the 0–100 scale. Overlapping comparisons connect them back to France; the individual 0–100 scores are never compared directly across exports. This improves integer precision but does not supply absolute counts or establish sampling accuracy. A country's own sharp peak can still compress its quieter weeks: Cabo Verde, Comoros and Haiti each reach 100 in an export yet retain weeks below the minimum score of 5.

The annual result is the **mean relative search-share index**, and per-capita attention is that index divided by population, expressed per million residents. These are **not absolute search counts**. Regional Trends indices cannot be subtracted to estimate foreign searches. The [methodological note](docs/methodology.md) defines calibration, aggregation, eligibility, population years, the population/GDP regression and limitations. The collected panel passes implementation and calibration checks; independent repeated-sample stability and publication-level empirical validation remain outstanding. See the [topic audit](docs/topic-audit.md) for corrected ambiguous identifiers and territorial qualifications.

## Project structure

```text
src/country_attention/
  acquisition.py    Cached public HTTP downloads and pagination
  countries.py      Research universe, ISO identities and conservative aliases
  economics.py      World Bank population, GDP and tourism
  trends.py         Audited original Google CSV import
  normalization.py  Shared-topic calibration and monthly aggregation
  analysis.py       Metrics, log model, residuals and sensitivity diagnostics
  pipeline.py       Dataset assembly, provenance and generated report
  cli.py            Collection and import commands
web/                React presentation page (Vite, d3 scales and SVG charts)
config/             Study settings, topic-review worksheet and manifest template
data/raw/           Original responses/exports, access checks and receipts
data/processed/     Rebuildable datasets, model output and report
tests/              Synthetic fixtures used only to verify the code
```

## Verification

```bash
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
pnpm --dir web typecheck
pnpm --dir web build
```

Tests cover country resolution, scope, date windows, shared and chained calibration, censoring, day weights, per-capita metrics, regression scale invariance, foreign-count safeguards, audited CSV imports, pagination and offline failure. Synthetic test fixtures never enter the research outputs. Dependencies are locked in `uv.lock`; there is no Google scraping dependency or credential requirement for the supplied snapshot.

The rankings are exploratory and apply only to eligible entities. Very small populations can produce large per-capita values. Publication requires repeated independent samples, alternative-anchor sensitivity and attention to excluded countries. In particular, the bottom 20 are not established as the least-searched countries among all 197 entities.
