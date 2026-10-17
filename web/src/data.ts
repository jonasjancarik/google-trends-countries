import { csvParse } from "d3-dsv";
import type { Topology } from "topojson-specification";

export type Country = {
  iso3: string;
  country: string;
  unMember: boolean;
  membership: string;
  region: string;
  incomeGroup: string | null;
  population: number | null;
  populationYear: number | null;
  populationSource: string;
  gdp: number | null;
  gdpYear: number | null;
  gdpPerCapita: number | null;
  attention: number | null;
  perMillion: number | null;
  vsExpected: number | null;
  peakShare: number | null;
  perMillionWithoutPeak: number | null;
  eligible: boolean;
  status: string;
  raw: Record<string, string>;
};

export type Month = { iso3: string; month: string; attention: number | null; lowResolution: boolean };

export type Regression = {
  status: string;
  n: number;
  r_squared: number;
  coefficients: { const: number; population: number; gdp_usd: number };
};

export type Provenance = {
  as_of: string;
  window_start: string;
  window_end: string;
  anchor_iso3: string;
  universe_count: number;
  un_members: number;
  ranked_countries: number;
  google_export_count: number;
  country_topics_with_exports: number;
};

export type Snapshot = {
  countries: Country[];
  byIso: Map<string, Country>;
  monthly: Map<string, Month[]>;
  months: string[];
  regression: Regression;
  provenance: Provenance;
  world: Topology;
};

const num = (value: string | undefined) => {
  if (value === undefined || value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const REGION_LABELS: Record<string, string> = {
  "Not covered by World Bank": "Outside World Bank regions",
};

async function fetchText(path: string) {
  const response = await fetch(`${import.meta.env.BASE_URL}data/${path}`);
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status})`);
  return response.text();
}

export async function loadSnapshot(): Promise<Snapshot> {
  const [rankingsText, monthlyText, regressionText, provenanceText, worldText] = await Promise.all([
    fetchText("rankings.csv"),
    fetchText("monthly_attention.csv"),
    fetchText("regression.json"),
    fetchText("provenance.json"),
    fetchText("world_110m.json"),
  ]);

  const countries: Country[] = csvParse(rankingsText).map((row) => {
    const region = (row.region ?? "").trim();
    const raw = { ...row } as Record<string, string>;
    return {
      iso3: row.iso3!,
      country: row.country!,
      unMember: row.core_un_member === "True",
      membership: row.membership ?? "",
      region: REGION_LABELS[region] ?? region,
      incomeGroup: row.income_group?.trim() || null,
      population: num(row.population),
      populationYear: num(row.population_year),
      populationSource: row.population_source ?? "",
      gdp: num(row.gdp_usd),
      gdpYear: num(row.gdp_usd_year),
      gdpPerCapita: num(row.gdp_per_capita_usd),
      attention: num(row.relative_attention),
      perMillion: num(row.attention_per_million),
      vsExpected: num(row.adjusted_ratio),
      peakShare: num(row.peak_month_share),
      perMillionWithoutPeak: num(row.per_capita_without_peak),
      eligible: row.ranking_status === "Eligible" && num(row.per_capita_rank) !== null,
      status: row.ranking_status ?? "",
      raw,
    };
  });

  const monthly = new Map<string, Month[]>();
  const monthSet = new Set<string>();
  for (const row of csvParse(monthlyText)) {
    const entry: Month = {
      iso3: row.iso3!,
      month: row.month!,
      attention: num(row.relative_attention),
      lowResolution: row.low_resolution === "True",
    };
    monthSet.add(entry.month);
    const list = monthly.get(entry.iso3) ?? [];
    list.push(entry);
    monthly.set(entry.iso3, list);
  }

  return {
    countries,
    byIso: new Map(countries.map((c) => [c.iso3, c])),
    monthly,
    months: [...monthSet].sort(),
    regression: JSON.parse(regressionText),
    provenance: JSON.parse(provenanceText),
    world: JSON.parse(worldText),
  };
}

/** Rank by descending value among the given countries; missing values get no rank. */
export function rankBy(countries: Country[], value: (c: Country) => number | null) {
  const ranks = new Map<string, number>();
  const sorted = countries
    .filter((c) => c.eligible && value(c) !== null)
    .sort((a, b) => value(b)! - value(a)!);
  let previous: number | null = null;
  let rank = 0;
  sorted.forEach((c, index) => {
    const v = value(c)!;
    if (v !== previous) rank = index + 1;
    previous = v;
    ranks.set(c.iso3, rank);
  });
  return ranks;
}

/** Approximate centres for countries too small to appear in the 110m world outline. */
export const SMALL_STATES: Record<string, [number, number]> = {
  AND: [1.52, 42.51],
  ATG: [-61.8, 17.08],
  BHR: [50.56, 26.07],
  BRB: [-59.54, 13.19],
  GRD: [-61.68, 12.12],
  VAT: [12.45, 41.9],
  KIR: [173, 1.4],
  XKX: [20.9, 42.6],
  LIE: [9.55, 47.16],
  MDV: [73.5, 3.2],
  MLT: [14.4, 35.9],
  MHL: [171.2, 7.1],
  FSM: [158.2, 6.9],
  MCO: [7.42, 43.74],
  NRU: [166.93, -0.52],
  PLW: [134.58, 7.51],
  KNA: [-62.78, 17.36],
  LCA: [-60.98, 13.91],
  VCT: [-61.2, 13.25],
  SMR: [12.46, 43.94],
  SYC: [55.45, -4.68],
  SGP: [103.82, 1.35],
  TON: [-175.2, -21.18],
  TUV: [179.2, -8.52],
};
