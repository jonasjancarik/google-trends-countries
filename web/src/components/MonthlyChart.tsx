import { scaleLinear, scaleLog, scalePoint } from "d3-scale";
import { line } from "d3-shape";
import { useState } from "react";
import type { Country, Month } from "../data";
import { fmtIndex, fmtMonth, fmtTick, logTicks } from "../format";
import { useWidth } from "../hooks";
import { SERIES } from "../scales";
import { Tooltip } from "./Tooltip";

export type MonthlyMode = "own" | "shared";

type Props = {
  countries: Country[];
  monthly: Map<string, Month[]>;
  months: string[];
  mode: MonthlyMode;
};

type Series = { country: Country; color: string; values: (number | null)[] };

export function MonthlyChart({ countries, monthly, months, mode }: Props) {
  const [ref, width] = useWidth<HTMLDivElement>(900);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const narrow = width < 560;
  const M = { top: 20, right: narrow ? 16 : 132, bottom: 34, left: 48 };
  const height = narrow ? 300 : 360;

  const series: Series[] = countries.map((country, i) => {
    const byMonth = new Map((monthly.get(country.iso3) ?? []).map((m) => [m.month, m.attention]));
    const raw = months.map((m) => byMonth.get(m) ?? null);
    const known = raw.filter((v): v is number => v !== null);
    const mean = known.reduce((a, b) => a + b, 0) / (known.length || 1);
    const values = mode === "own" ? raw.map((v) => (v === null ? null : (v / mean) * 100)) : raw;
    return { country, color: SERIES[i], values };
  });

  const all = series.flatMap((s) => s.values).filter((v): v is number => v !== null && v > 0);
  const x = scalePoint<string>()
    .domain(months)
    .range([M.left, width - M.right]);
  const lo = Math.min(...all, mode === "own" ? 60 : Infinity);
  const hi = Math.max(...all, mode === "own" ? 140 : 0);
  const y =
    mode === "own"
      ? scaleLinear()
          .domain([Math.min(0, lo), hi * 1.08])
          .nice()
          .range([height - M.bottom, M.top])
      : scaleLog()
          .domain([lo / 1.3, hi * 1.3])
          .range([height - M.bottom, M.top]);
  const yTicks = mode === "own" ? (y as ReturnType<typeof scaleLinear>).ticks(5) : logTicks(lo / 1.3, hi * 1.3, [1, 3]);

  const path = line<number | null>()
    .defined((v) => v !== null && v > 0)
    .x((_, i) => x(months[i])!)
    .y((v) => y(v!));

  // Spread end labels apart so they do not overlap.
  const ends = series
    .map((s) => {
      const last = [...s.values].reverse().find((v) => v !== null && v > 0) ?? null;
      return { s, y: last === null ? null : y(last) };
    })
    .filter((e): e is { s: Series; y: number } => e.y !== null)
    .sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 16);

  const onMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const mx = event.clientX - event.currentTarget.getBoundingClientRect().left;
    const step = x.step();
    const index = Math.round((mx - M.left) / step);
    setHoverIndex(index >= 0 && index < months.length ? index : null);
  };

  const showEvery = width < 480 ? 3 : width < 760 ? 2 : 1;

  return (
    <div className="chart" ref={ref}>
      <svg width={width} height={height} onPointerMove={onMove} onPointerLeave={() => setHoverIndex(null)}>
        {yTicks.map((t) => (
          <g key={t}>
            <line className="grid" x1={M.left} x2={width - M.right} y1={y(t)} y2={y(t)} />
            <text className="tick" x={M.left - 10} y={y(t) + 4} textAnchor="end">
              {fmtTick(t)}
            </text>
          </g>
        ))}
        {mode === "own" && <line className="baseline-100" x1={M.left} x2={width - M.right} y1={y(100)} y2={y(100)} />}
        {months.map((m, i) =>
          i % showEvery === 0 ? (
            <text key={m} className="tick" x={x(m)} y={height - M.bottom + 20} textAnchor="middle">
              {fmtMonth(m)}
            </text>
          ) : null,
        )}
        {hoverIndex !== null && (
          <line className="crosshair" x1={x(months[hoverIndex])} x2={x(months[hoverIndex])} y1={M.top} y2={height - M.bottom} />
        )}
        {series.map((s) => (
          <g key={s.country.iso3}>
            <path className="series-line" d={path(s.values) ?? undefined} style={{ stroke: s.color }} />
            {s.values.map((v, i) =>
              v !== null && v > 0 && (hoverIndex === i || s.values[i - 1] == null || s.values[i + 1] == null) ? (
                <circle key={i} className="series-point" cx={x(months[i])} cy={y(v)} r={4} style={{ fill: s.color }} />
              ) : null,
            )}
          </g>
        ))}
        {!narrow &&
          ends.map(({ s, y: ly }) => (
            <g key={`end${s.country.iso3}`}>
              <circle cx={width - M.right + 12} cy={ly} r={4} style={{ fill: s.color }} />
              <text className="end-label" x={width - M.right + 22} y={ly + 4}>
                {s.country.country.length > 15 ? `${s.country.country.slice(0, 14)}…` : s.country.country}
              </text>
            </g>
          ))}
      </svg>
      {hoverIndex !== null && (
        <Tooltip x={x(months[hoverIndex])!} y={M.top + 10} bounds={width}>
          <div className="tooltip-title">{fmtMonth(months[hoverIndex], "long")}</div>
          <dl>
            {series.map((s) => (
              <div key={s.country.iso3} className="tooltip-row">
                <dt>
                  <span className="key-dot" style={{ background: s.color }} />
                  {s.country.country}
                </dt>
                <dd>{s.values[hoverIndex] === null ? "No data" : fmtIndex(s.values[hoverIndex])}</dd>
              </div>
            ))}
          </dl>
        </Tooltip>
      )}
    </div>
  );
}
