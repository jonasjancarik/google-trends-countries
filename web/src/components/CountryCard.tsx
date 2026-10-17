import type { Country, Month } from "../data";
import { fmtIndex, fmtMoney, fmtMonth, fmtPeople, fmtPercent, fmtTimes, ordinal } from "../format";

type Props = {
  country: Country;
  monthly: Month[];
  ranks: { perMillion: Map<string, number>; total: Map<string, number>; expected: Map<string, number> };
  rankedCount: number;
  compared: boolean;
  onCompare: () => void;
};

export function CountryCard({ country, monthly, ranks, rankedCount, compared, onCompare }: Props) {
  const rank = ranks.perMillion.get(country.iso3);
  const busiest = monthly.reduce<Month | null>(
    (best, m) => (m.attention !== null && (!best || m.attention > best.attention!) ? m : best),
    null,
  );
  return (
    <article className="card" aria-live="polite">
      <header>
        <p className="card-region">
          {country.region}
          {!country.unMember && ` · ${country.membership === "UN observer" ? "UN observer" : "Not a UN member"}`}
        </p>
        <h3>{country.country}</h3>
      </header>
      {country.eligible ? (
        <>
          <div className="card-headline">
            <span className="card-number">{fmtIndex(country.perMillion)}</span>
            <span className="card-unit">
              per million residents
              <br />
              <strong>{rank ? `${ordinal(rank)} of ${rankedCount}` : "Unranked"}</strong>
            </span>
          </div>
          <dl className="card-facts">
            <dt>Total search interest</dt>
            <dd>
              {fmtIndex(country.attention)} <span className="muted">· {ordinal(ranks.total.get(country.iso3)!)}</span>
            </dd>
            <dt>Versus prediction</dt>
            <dd>{country.vsExpected === null ? <span className="muted">Not in the model</span> : fmtTimes(country.vsExpected)}</dd>
            {country.vsExpected !== null && country.modelYear !== null && (
              <><dt>Model population and GDP year</dt><dd>{country.modelYear}</dd></>
            )}
            <dt>Population</dt>
            <dd>
              {fmtPeople(country.population)}
              {country.populationYear && <span className="muted"> · {country.populationYear}</span>}
            </dd>
            <dt>GDP</dt>
            <dd>
              {fmtMoney(country.gdp)}
              {country.gdpYear && <span className="muted"> · {country.gdpYear}</span>}
            </dd>
            {busiest && (
              <>
                <dt>Busiest month</dt>
                <dd>
                  {fmtMonth(busiest.month, "long")}{" "}
                  <span className="muted">· {fmtPercent(country.peakShare)} of the year</span>
                </dd>
              </>
            )}
          </dl>
          <button type="button" className="button" onClick={onCompare} disabled={compared}>
            {compared ? "Already in the monthly comparison" : "Compare month by month"}
          </button>
        </>
      ) : (
        <p className="card-empty">
          The exported scores for {country.country} did not meet the study&apos;s precision or completeness rules,
          so it has no published score or rank. Its population is {fmtPeople(country.population)}.
        </p>
      )}
      {country.populationSource && country.populationSource !== "World Bank" && (
        <p className="card-note">Population from {country.populationSource}, not the World Bank.</p>
      )}
    </article>
  );
}
