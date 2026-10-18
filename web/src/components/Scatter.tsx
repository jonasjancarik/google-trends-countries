import { extent } from "d3-array";
import { scaleLog } from "d3-scale";
import { useMemo, useState } from "react";
import type { Country } from "../data";
import { fmtMoney, fmtTick, logTicks } from "../format";
import { useWidth, type Hover } from "../hooks";
import { SERIES } from "../scales";
import { CountryTooltip } from "./Tooltip";

export type XMeasure = "population" | "gdp" | "gdpPerCapita";

const MEASURES = {
  population: { label: "Population", axis: "Population →" },
  gdp: { label: "GDP", axis: "GDP, current US$ →" },
  gdpPerCapita: { label: "GDP per capita", axis: "GDP per capita, current US$ →" },
};

type Props = {
  countries: Country[];
  measure: XMeasure;
  ranks: Map<string, number>;
  picked: string[];
  annotate: string[];
  onSelect: (iso3: string) => void;
};

const M = { top: 16, right: 20, bottom: 44, left: 52 };

export function fitLogLog(points: { x: number; y: number }[]) {
  const n = points.length;
  const lx = points.map((p) => Math.log(p.x));
  const ly = points.map((p) => Math.log(p.y));
  const mx = lx.reduce((a, b) => a + b, 0) / n;
  const my = ly.reduce((a, b) => a + b, 0) / n;
  let sxy = 0;
  let sxx = 0;
  let syy = 0;
  for (let i = 0; i < n; i++) {
    sxy += (lx[i] - mx) * (ly[i] - my);
    sxx += (lx[i] - mx) ** 2;
    syy += (ly[i] - my) ** 2;
  }
  const slope = sxy / sxx;
  return { slope, intercept: my - slope * mx, r2: (sxy * sxy) / (sxx * syy) };
}

export function Scatter({ countries, measure, ranks, picked, annotate, onSelect }: Props) {
  const [ref, width] = useWidth<HTMLDivElement>(900);
  const [hover, setHover] = useState<Hover<Country>>(null);
  const height = Math.min(540, Math.max(340, Math.round(width * 0.56)));

  const xOf = (c: Country) => c[measure];
  const { label, axis } = MEASURES[measure];
  const points = useMemo(
    () =>
      countries
        .filter((c) => c.eligible && (xOf(c) ?? 0) > 0 && (c.attention ?? 0) > 0)
        .map((c) => ({ c, x: xOf(c)!, y: c.attention! })),
    [countries, measure],
  );

  const [x0, x1] = extent(points, (p) => p.x) as [number, number];
  const [y0, y1] = extent(points, (p) => p.y) as [number, number];
  const x = scaleLog()
    .domain([x0 / 1.6, x1 * 1.6])
    .range([M.left, width - M.right]);
  const y = scaleLog()
    .domain([y0 / 1.6, y1 * 1.6])
    .range([height - M.bottom, M.top]);
  const fit = points.length > 2 ? fitLogLog(points) : null;
  const fitY = (v: number) => Math.exp(fit!.intercept + fit!.slope * Math.log(v));

  const xTicks = logTicks(x.domain()[0], x.domain()[1], [1]);
  const yTicks = logTicks(y.domain()[0], y.domain()[1], [1]);

  const onMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const mx = event.clientX - box.left;
    const my = event.clientY - box.top;
    let best: (typeof points)[number] | null = null;
    let bestDistance = 24 * 24;
    for (const p of points) {
      const d = (x(p.x) - mx) ** 2 + (y(p.y) - my) ** 2;
      if (d < bestDistance) {
        bestDistance = d;
        best = p;
      }
    }
    setHover(best ? { item: best.c, x: x(best.x), y: y(best.y) } : null);
  };

  const pickedPoints = picked
    .map((iso, i) => ({ p: points.find((p) => p.c.iso3 === iso), color: SERIES[i] }))
    .filter((d) => d.p);
  const labelled = points.filter((p) => annotate.includes(p.c.iso3) && !picked.includes(p.c.iso3));

  return (
    <div className="chart" ref={ref}>
      <svg
        width={width}
        height={height}
        onPointerMove={onMove}
        onPointerLeave={() => setHover(null)}
        onClick={() => hover && onSelect(hover.item.iso3)}
        role="img"
        aria-label={`Scatterplot of search interest against ${label}`}
      >
        {xTicks.map((t) => (
          <g key={`x${t}`}>
            <line className="grid" x1={x(t)} x2={x(t)} y1={M.top} y2={height - M.bottom} />
            <text className="tick" x={x(t)} y={height - M.bottom + 18} textAnchor="middle">
              {measure === "population" ? fmtTick(t) : `$${fmtTick(t)}`}
            </text>
          </g>
        ))}
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line className="grid" x1={M.left} x2={width - M.right} y1={y(t)} y2={y(t)} />
            <text className="tick" x={M.left - 10} y={y(t) + 4} textAnchor="end">
              {fmtTick(t)}
            </text>
          </g>
        ))}
        <text className="axis-title" x={width - M.right} y={height - 6} textAnchor="end">
          {axis}
        </text>
        <text className="axis-title" x={M.left} y={M.top - 4}>
          ↑ Search interest (France = 100)
        </text>
        {fit && (
          <line
            className="fit-line"
            x1={x(x.domain()[0])}
            y1={y(fitY(x.domain()[0]))}
            x2={x(x.domain()[1])}
            y2={y(fitY(x.domain()[1]))}
          />
        )}
        {points.map((p) => (
          <circle key={p.c.iso3} className="dot" cx={x(p.x)} cy={y(p.y)} r={4.5} />
        ))}
        {labelled.map((p) => (
          <g key={`l${p.c.iso3}`}>
            <circle className="dot is-labelled" cx={x(p.x)} cy={y(p.y)} r={4.5} />
            <text className="dot-label" x={x(p.x) + 8} y={y(p.y) + 4}>
              {p.c.country}
            </text>
          </g>
        ))}
        {pickedPoints.map(({ p, color }) => (
          <g key={`p${p!.c.iso3}`}>
            <circle className="dot is-picked" cx={x(p!.x)} cy={y(p!.y)} r={6.5} style={{ fill: color }} />
            <text className="dot-label is-picked" x={x(p!.x) + 10} y={y(p!.y) + 4}>
              {p!.c.country}
            </text>
          </g>
        ))}
        {hover && <circle className="dot-hover" cx={hover.x} cy={hover.y} r={8} />}
      </svg>
      {hover && (
        <CountryTooltip country={hover.item} rank={ranks.get(hover.item.iso3)} x={hover.x} y={hover.y} bounds={width}>
          {measure === "gdpPerCapita" && (
            <span>GDP per capita: {fmtMoney(hover.item.gdpPerCapita)} ({hover.item.raw.gdp_per_capita_usd_year})</span>
          )}
        </CountryTooltip>
      )}
      {fit && (
        <p className="chart-note">
          The fitted line captures {Math.round(fit.r2 * 100)}% of the variation in log search interest across the{" "}
          {points.length} countries shown. It compares {label === "Population" ? "population" : label} alone with search
          interest, without accounting for other country differences.
        </p>
      )}
    </div>
  );
}
