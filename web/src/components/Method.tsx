import type { Country, Snapshot } from "../data";

export function Method({ data, unranked }: { data: Snapshot; unranked: Country[] }) {
  const { provenance } = data;
  const missing = unranked.map((c) => c.country);
  const list = missing.length > 1 ? `${missing.slice(0, -1).join(", ")} and ${missing.at(-1)}` : missing[0];
  const base = `${import.meta.env.BASE_URL}data/`;
  return (
    <section id="method" className="section method">
      <div className="section-head">
        <div>
          <h2>How this was measured</h2>
          <p className="lede">The short version of the method, and what the numbers can and cannot tell you.</p>
        </div>
      </div>
      <div className="method-grid">
        <div>
          <h3>What the index is</h3>
          <p>
            Google Trends shows how popular a search topic is as a share of all searches, rescaled so the busiest moment
            in a comparison equals 100. Each country was looked up as a reviewed Google topic, which gathers searches in
            many languages and reduces mix-ups such as Georgia the US state or Turkey the bird. Google&apos;s topic
            definitions are proprietary, so this does not capture every search concerning a country.
          </p>
          <p>
            Google limits the number of topics in one comparison, so the study links {provenance.google_export_count} separate
            comparisons through the countries they share. That puts every country on one scale, where France&apos;s
            yearly average equals 100. Dividing by population and multiplying by a million gives the per-resident figure.
          </p>
        </div>
        <div>
          <h3>What it is not</h3>
          <p>
            These are not counts of searches or of people. The figures include searches from everywhere, the country
            itself included. Google&apos;s figures for individual regions use different baselines, so they cannot be
            subtracted to find how much of the interest comes from abroad; this page does not try.
          </p>
          <p>
            Per-resident values favour very small countries: a little worldwide interest divided among a few thousand
            people becomes a large number. The prediction offers a second benchmark, accounting for both population
            and economic output per person. Neither benchmark establishes how much attention a country deserves.
          </p>
        </div>
        <div>
          <h3>Who is missing, and why</h3>
          <p>
            {missing.length ? (
              <>
                {list} {missing.length === 1 ? "has" : "have"} no rank because at least one weekly score was below 5
                on the exported 0–100 scale. This is the study&apos;s conservative rule, not a Google search-count
                threshold. Annual precision diagnostics are available below; they do not yet replace that rule.
              </>
            ) : (
              "Every country shown met the measurement requirements."
            )}
          </p>
          <p>
            Population and GDP come from the World Bank, mostly for 2025. Taiwan uses its official household register.
            The Holy See row uses the 882 residents of Vatican City, matching the place people search for. Kosovo is
            included as a separate entity; this is a coverage choice, not a position on its status.
          </p>
        </div>
        <div>
          <h3>How sure can we be</h3>
          <p>
            The main rankings use exports collected on{" "}
            {new Date(provenance.as_of).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}. Google samples searches, so a
            repeat collection could reorder countries with similar scores. The downloads below show how ranks change
            under alternative calculation choices and how integer rounding affects annual values. These ranges do not
            include Google&apos;s sampling uncertainty and are not confidence intervals. Treat the rankings as preliminary.
          </p>
          <p className="links">
            <a href="https://support.google.com/trends/answer/4365533?hl=en">How Google normalises Trends data</a>
            <a href="https://data.worldbank.org/indicator/SP.POP.TOTL">World Bank population data</a>
            <a href="https://arxiv.org/abs/2007.13861">Research on linking Trends comparisons</a>
          </p>
          <p className="links">
            <a href={`${base}rankings.csv`} download>
              Download all country data (CSV)
            </a>
            <a href={`${base}monthly_attention.csv`} download>
              Download monthly values (CSV)
            </a>
            <a href={`${base}ranking_sensitivity.csv`} download>Download rank sensitivity and annual precision (CSV)</a>
            <a href={`${base}sensitivity.json`} download>Download sensitivity checks, including failed checks (JSON)</a>
            <a href={`${base}methodology.md`}>Read the full methodology and rationale</a>
            <a href={`${base}collection.md`}>Read the repeated-sample collection protocol</a>
          </p>
          {provenance.repeat_panel_comparison_available && (
            <p>
              Separate collections have also been compared using fixed populations and the same eligible countries.
              Their observed rank ranges are descriptive; distinct collection dates do not prove independent samples.
              {" "}<a href={`${base}panel_comparison.csv`} download>Download the repeat comparison (CSV)</a>
              {" · "}<a href={`${base}panel_comparison.json`} download>Collection dates and comparison details (JSON)</a>
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
