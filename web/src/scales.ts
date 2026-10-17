import { scaleThreshold } from "d3-scale";
import type { Country } from "./data";

export type MapMetric = "perMillion" | "vsExpected";

export const SEQ_THRESHOLDS = [0.1, 0.3, 1, 3, 10, 30];
export const DIV_THRESHOLDS = [1 / 3, 1 / 2, 1 / 1.25, 1.25, 2, 3];

const classes = (prefix: string) => Array.from({ length: 7 }, (_, i) => `var(--${prefix}-${i})`);

export const seqColor = scaleThreshold<number, string>().domain(SEQ_THRESHOLDS).range(classes("seq"));
export const divColor = scaleThreshold<number, string>().domain(DIV_THRESHOLDS).range(classes("div"));

export const metricValue = (c: Country, metric: MapMetric) =>
  c.eligible ? (metric === "perMillion" ? c.perMillion : c.vsExpected) : null;

export const fillFor = (c: Country | undefined, metric: MapMetric) => {
  if (!c) return "var(--land-empty)";
  const value = metricValue(c, metric);
  if (value === null) return "url(#nodata-hatch)";
  return metric === "perMillion" ? seqColor(value) : divColor(value);
};

export const LEGENDS: Record<MapMetric, { label: string; title: string; low: string; high: string }> = {
  perMillion: {
    title: "Search interest per million residents",
    label: "Index per million residents",
    low: "Less per resident",
    high: "More per resident",
  },
  vsExpected: {
    title: "Compared with what population and economy predict",
    label: "Actual ÷ predicted",
    low: "Less than predicted",
    high: "More than predicted",
  },
};

/** Series colours for compared countries, assigned in fixed order. */
export const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"];
