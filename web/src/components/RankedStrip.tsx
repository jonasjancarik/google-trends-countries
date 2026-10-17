import { scaleLog } from "d3-scale";
import type { Country } from "../data";
import { useWidth } from "../hooks";

type Props = {
  rows: Country[];
  value: (c: Country) => number;
  domain: [number, number];
  ranks: Map<string, number>;
  format: (v: number) => string;
  focus: string | null;
  onSelect: (iso3: string) => void;
  /** Draw a reference line, e.g. 1× for "as predicted". */
  reference?: { value: number; label: string };
  tone?: "seq" | "above" | "below";
};

/** A ranked list with each value placed as a dot on a shared logarithmic axis. */
export function RankedStrip({ rows, value, domain, ranks, format, focus, onSelect, reference, tone = "seq" }: Props) {
  const [ref, width] = useWidth<HTMLDivElement>(320);
  const x = scaleLog().domain(domain).range([6, Math.max(60, width - 6)]).clamp(true);
  return (
    <ol className={`strip strip-${tone}`}>
      {rows.map((c) => {
        const v = value(c);
        const rank = ranks.get(c.iso3);
        return (
          <li key={c.iso3} className={c.iso3 === focus ? "is-focus" : undefined}>
            <button type="button" onClick={() => onSelect(c.iso3)}>
              <span className="strip-rank">{rank}</span>
              <span className="strip-name">{c.country}</span>
              <span className="strip-track" ref={rows[0] === c ? ref : undefined}>
                <svg width={width} height={18} aria-hidden="true">
                  <line className="strip-rail" x1={0} x2={width} y1={9} y2={9} />
                  {reference && (
                    <line className="strip-ref" x1={x(reference.value)} x2={x(reference.value)} y1={2} y2={16} />
                  )}
                  {reference && (
                    <line className="strip-stem" x1={x(reference.value)} x2={x(v)} y1={9} y2={9} />
                  )}
                  <circle className="strip-dot" cx={x(v)} cy={9} r={5} />
                </svg>
              </span>
              <span className="strip-value">{format(v)}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
