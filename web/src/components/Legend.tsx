import { fmtIndex } from "../format";
import { DIV_THRESHOLDS, LEGENDS, SEQ_THRESHOLDS, type MapMetric } from "../scales";

export function MapLegend({ metric }: { metric: MapMetric }) {
  const legend = LEGENDS[metric];
  const thresholds = metric === "perMillion" ? SEQ_THRESHOLDS : DIV_THRESHOLDS;
  const prefix = metric === "perMillion" ? "seq" : "div";
  const label = (v: number) => (metric === "perMillion" ? fmtIndex(v) : `${fmtIndex(v, 2)}×`);
  return (
    <div className="legend" aria-label={legend.title}>
      <div className="legend-label">{legend.label}</div>
      <div className="legend-scale">
        {Array.from({ length: 7 }, (_, i) => (
          <span key={i} className="legend-swatch" style={{ background: `var(--${prefix}-${i})` }} />
        ))}
      </div>
      <div className="legend-ticks">
        {thresholds.map((t, i) => (
          <span key={t} style={{ left: `${((i + 1) / 7) * 100}%` }}>
            {label(t)}
          </span>
        ))}
      </div>
      <div className="legend-ends">
        <span>{legend.low}</span>
        <span>{legend.high}</span>
      </div>
      <div className="legend-nodata">
        <span className="legend-swatch is-hatch" />
        {metric === "perMillion" ? "Too few searches to rank" : "Not in the model or too few searches"}
      </div>
    </div>
  );
}
