import type { ReactNode } from "react";
import type { Country } from "../data";
import { fmtIndex, fmtPeople, fmtTimes, ordinal } from "../format";

export function Tooltip({ x, y, bounds, children }: { x: number; y: number; bounds: number; children: ReactNode }) {
  const flip = x > bounds - 240;
  return (
    <div
      className="tooltip"
      style={{ left: flip ? undefined : x + 16, right: flip ? bounds - x + 16 : undefined, top: y + 12 }}
    >
      {children}
    </div>
  );
}

export function CountryTooltip({
  country,
  rank,
  x,
  y,
  bounds,
  children,
}: {
  country: Country;
  rank?: number;
  x: number;
  y: number;
  bounds: number;
  children?: ReactNode;
}) {
  return (
    <Tooltip x={x} y={y} bounds={bounds}>
      <div className="tooltip-title">{country.country}</div>
      {country.eligible ? (
        <dl>
          <dt>Per million residents</dt>
          <dd>{fmtIndex(country.perMillion)}</dd>
          <dt>Rank per resident</dt>
          <dd>{rank ? ordinal(rank) : "—"}</dd>
          <dt>Versus prediction</dt>
          <dd>{country.vsExpected === null ? "Not in the model" : fmtTimes(country.vsExpected)}</dd>
          <dt>Population</dt>
          <dd>{fmtPeople(country.population)}</dd>
        </dl>
      ) : (
        <p className="tooltip-note">Too few searches to measure reliably, so it has no rank.</p>
      )}
      {children}
    </Tooltip>
  );
}
