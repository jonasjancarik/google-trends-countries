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
            many languages and avoids mix-ups such as Georgia the US state or Turkey the bird.
          </p>
          <p>
            Google only compares five topics at a time, so the study links {provenance.google_export_count} separate
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
            people becomes a large number. The comparison with a prediction from population and GDP is a second view
            that accounts for this.
          </p>
        </div>
        <div>
          <h3>Who is missing, and why</h3>
          <p>
            {missing.length ? (
              <>
                {list} {missing.length === 1 ? "has" : "have"} no rank. Some weeks fell below the level Google can
                report precisely, so a yearly average would not be trustworthy. They are left out instead of being given
                a low score.
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
            This is one sample of Google&apos;s data, collected on{" "}
            {new Date(provenance.as_of).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}. Google samples searches, so a
            repeat collection could reorder countries with similar scores. Large gaps between countries are more
            trustworthy than small differences in position. Treat the rankings as
            preliminary until repeated samples confirm them.
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
          </p>
        </div>
      </div>
    </section>
  );
}
