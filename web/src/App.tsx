import { useEffect, useMemo, useState } from "react";
import { rankBy, type Country, type Snapshot } from "./data";
import { fmtIndex, fmtMonth, fmtPeople, fmtTimes } from "./format";
import { LEGENDS, type MapMetric } from "./scales";
import { CountryCard } from "./components/CountryCard";
import { MapLegend } from "./components/Legend";
import { MonthlyChart, type MonthlyMode } from "./components/MonthlyChart";
import { CountryPicker } from "./components/CountryPicker";
import { RankedStrip } from "./components/RankedStrip";
import { RankingsTable } from "./components/RankingsTable";
import { Scatter, type XMeasure } from "./components/Scatter";
import { Segmented } from "./components/Segmented";
import { ThemeToggle } from "./components/ThemeToggle";
import { Method } from "./components/Method";
import { WorldMap } from "./components/WorldMap";

const NAV = [
  ["map", "Map"],
  ["rankings", "Rankings"],
  ["size", "Size"],
  ["surprises", "Surprises"],
  ["over-time", "Over time"],
  ["all", "All countries"],
  ["method", "Method"],
] as const;

export function App({ data }: { data: Snapshot }) {
  const { provenance, regression } = data;
  const [extended, setExtended] = useState(false);
  const [metric, setMetric] = useState<MapMetric>("perMillion");
  const [measure, setMeasure] = useState<XMeasure>("population");
  const [mode, setMode] = useState<MonthlyMode>("own");
  const [picked, setPicked] = useState<string[]>(["CZE", "FRA", "USA"]);
  const [focus, setFocus] = useState<string | null>(null);

  const countries = useMemo(
    () => data.countries.filter((c) => extended || c.unMember),
    [data.countries, extended],
  );
  const inView = useMemo(() => new Map(countries.map((c) => [c.iso3, c])), [countries]);
  const ranks = useMemo(() => rankBy(countries, (c) => c.perMillion), [countries]);
  const totalRanks = useMemo(() => rankBy(countries, (c) => c.attention), [countries]);
  const expectedRanks = useMemo(() => rankBy(countries, (c) => c.vsExpected), [countries]);
  const eligible = countries.filter((c) => c.eligible && c.perMillion !== null);
  const byPerMillion = [...eligible].sort((a, b) => b.perMillion! - a.perMillion!);
  const top = byPerMillion.slice(0, 20);
  const bottom = byPerMillion.slice(-20).reverse();
  const modelled = eligible.filter((c) => c.vsExpected !== null).sort((a, b) => b.vsExpected! - a.vsExpected!);
  const above = modelled.slice(0, 12);
  const below = modelled.slice(-12).reverse();
  const unranked = countries.filter((c) => !c.eligible);
  const regions = [...new Set(countries.map((c) => c.region))].sort();

  const leader = byPerMillion[0];
  const france = data.byIso.get(provenance.anchor_iso3)!;
  const focusCountry = (focus && inView.get(focus)) || leader;
  const bottomAfrica = bottom.filter((c) => c.region === "Sub-Saharan Africa").length;

  useEffect(() => {
    // The page renders after the data arrives, so jump to a linked section once it exists.
    const timer = setTimeout(() => {
      if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
    }, 60);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (focus && !inView.has(focus)) setFocus(null);
  }, [focus, inView]);

  const select = (iso3: string) => setFocus(iso3);
  const compare = (iso3: string) => {
    setPicked((list) => (list.includes(iso3) ? list : [...list, iso3].slice(-4)));
    document.getElementById("over-time")?.scrollIntoView({ behavior: "smooth" });
  };
  const pickedCountries = picked.map((iso) => data.byIso.get(iso)!).filter((c) => inView.has(c.iso3));

  const strongest = [...eligible].sort((a, b) => b.attention! - a.attention!).slice(0, 3);
  const annotate = [
    ...byPerMillion.slice(0, 2).map((c) => c.iso3),
    ...strongest.map((c) => c.iso3),
    ...(measure === "gdp" ? modelled.slice(0, 2).map((c) => c.iso3) : []),
  ];

  const period = `${fmtMonth(provenance.window_start.slice(0, 7), "long")} – ${fmtMonth(provenance.window_end.slice(0, 7), "long")}`;

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <a className="brand" href="#top">
            <span className="brand-mark" aria-hidden="true" />
            Country attention
          </a>
          <nav aria-label="Sections">
            {NAV.map(([id, label]) => (
              <a key={id} href={`#${id}`}>
                {label}
              </a>
            ))}
          </nav>
          <ThemeToggle />
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <p className="kicker">Worldwide Google searches · {period}</p>
          <h1>
            Which countries does the world look up most, <em>for their size?</em>
          </h1>
          <p className="dek">
            Twelve months of worldwide Google search interest in {provenance.universe_count} countries, set against how
            many people live in each one. Small, well-known places draw far more attention per resident than their size
            would suggest, while {bottomAfrica > 10 ? "many populous countries in Sub-Saharan Africa" : "several populous countries"} receive
            the least.
          </p>

          <div className="scope">
            <span className="scope-label">Countries shown</span>
            <Segmented
              value={extended ? "all" : "un"}
              onChange={(v) => setExtended(v === "all")}
              options={[
                { value: "un", label: `${provenance.un_members} UN members` },
                { value: "all", label: "Also Holy See, Palestine, Taiwan, Kosovo" },
              ]}
            />
          </div>

          <dl className="stats">
            <div>
              <dt>Most searched for per resident</dt>
              <dd className="stat-big">{leader.country}</dd>
              <dd className="stat-note">
                {fmtIndex(leader.perMillion)} per million residents, against {fmtIndex(france.perMillion)} for France
              </dd>
            </div>
            <div>
              <dt>Least searched for per resident</dt>
              <dd className="stat-big">{bottom[0].country}</dd>
              <dd className="stat-note">{fmtIndex(bottom[0].perMillion)} per million residents</dd>
            </div>
            <div>
              <dt>Explained by population and GDP</dt>
              <dd className="stat-big">{Math.round(regression.r_squared * 100)}%</dd>
              <dd className="stat-note">of the differences in total search interest, across {regression.n} countries</dd>
            </div>
            <div>
              <dt>Countries with a rank</dt>
              <dd className="stat-big">
                {eligible.length} <span className="stat-of">of {countries.length}</span>
              </dd>
              <dd className="stat-note">
                {unranked.length ? `${unranked.map((c) => c.country).join(", ")} had too few searches to measure` : "All measured"}
              </dd>
            </div>
          </dl>

          <aside className="explainer">
            <h2>How to read the numbers</h2>
            <p>
              Google reports relative search interest, not search counts. France is the yardstick: its average over the
              year is set to <strong>100</strong>. {leader.country} scores {fmtIndex(leader.attention)} on that scale, but
              with only {fmtPeople(leader.population)} residents that works out to{" "}
              <strong>{fmtIndex(leader.perMillion)} per million people</strong>. France, with {fmtPeople(france.population)},
              gets {fmtIndex(france.perMillion)}.
            </p>
          </aside>
        </section>

        <section id="map" className="section">
          <div className="section-head">
            <div>
              <h2>{LEGENDS[metric].title}</h2>
              <p className="lede">
                {metric === "perMillion"
                  ? "Each country is shaded by the search interest it receives for every person who lives there. Small states that the map cannot outline appear as circles. Click any country for details."
                  : "Blue countries are searched for more than their population and GDP predict; orange countries less. Hatched countries are not part of the prediction."}
              </p>
            </div>
            <Segmented
              value={metric}
              onChange={setMetric}
              options={[
                { value: "perMillion", label: "Per resident" },
                { value: "vsExpected", label: "Versus prediction" },
              ]}
            />
          </div>
          <div className="map-layout">
            <div>
              <WorldMap
                world={data.world}
                inView={inView}
                metric={metric}
                ranks={ranks}
                focus={focusCountry.iso3}
                onSelect={select}
              />
              <MapLegend metric={metric} />
            </div>
            <CountryCard
              country={focusCountry}
              monthly={data.monthly.get(focusCountry.iso3) ?? []}
              ranks={{ perMillion: ranks, total: totalRanks, expected: expectedRanks }}
              rankedCount={eligible.length}
              compared={picked.includes(focusCountry.iso3)}
              onCompare={() => compare(focusCountry.iso3)}
            />
          </div>
        </section>

        <section id="rankings" className="section">
          <div className="section-head">
            <div>
              <h2>Most and least searched for, per resident</h2>
              <p className="lede">
                The top of the list belongs to microstates and island nations, where a modest amount of worldwide interest
                is shared among very few people. Each dot sits on the same logarithmic scale, so every step to the right
                is a multiplication.
              </p>
            </div>
          </div>
          <div className="two-col">
            <div>
              <h3>Top 20</h3>
              <RankedStrip
                rows={top}
                value={(c) => c.perMillion!}
                domain={[bottom[0].perMillion! * 0.8, top[0].perMillion! * 1.2]}
                ranks={ranks}
                format={(v) => fmtIndex(v)}
                focus={focusCountry.iso3}
                onSelect={select}
              />
            </div>
            <div>
              <h3>Bottom 20</h3>
              <RankedStrip
                rows={bottom}
                value={(c) => c.perMillion!}
                domain={[bottom[0].perMillion! * 0.8, top[0].perMillion! * 1.2]}
                ranks={ranks}
                format={(v) => fmtIndex(v)}
                focus={focusCountry.iso3}
                onSelect={select}
              />
            </div>
          </div>
          <p className="footnote">
            Index per million residents. Countries with too few searches to measure reliably are left out rather than
            placed at the bottom, so this is the bottom of the measured list, not necessarily of the world.
          </p>
        </section>

        <section id="size" className="section">
          <div className="section-head">
            <div>
              <h2>Bigger, richer countries get searched for more</h2>
              <p className="lede">
                Total search interest rises steadily with a country&apos;s size. Each dot is a country; both axes use a
                logarithmic scale. Hover for details, or click a dot to show it on the map card.
              </p>
            </div>
            <Segmented
              value={measure}
              onChange={setMeasure}
              options={[
                { value: "population", label: "By population" },
                { value: "gdp", label: "By GDP" },
              ]}
            />
          </div>
          <Scatter
            countries={countries}
            measure={measure}
            ranks={ranks}
            picked={pickedCountries.map((c) => c.iso3)}
            annotate={annotate}
            onSelect={select}
          />
        </section>

        <section id="surprises" className="section">
          <div className="section-head">
            <div>
              <h2>Searched for more, or less, than expected</h2>
              <p className="lede">
                Knowing a country&apos;s population and GDP lets us predict how much search interest it should get. These
                countries are furthest from that prediction. A value of 3× means three times the predicted interest. The
                model can describe the gap, but not explain what causes it.
              </p>
            </div>
          </div>
          <div className="two-col">
            <div>
              <h3>More than predicted</h3>
              <RankedStrip
                rows={above}
                value={(c) => c.vsExpected!}
                domain={[1 / 6, 6]}
                ranks={expectedRanks}
                format={fmtTimes}
                focus={focusCountry.iso3}
                onSelect={select}
                reference={{ value: 1, label: "As predicted" }}
                tone="above"
              />
            </div>
            <div>
              <h3>Less than predicted</h3>
              <RankedStrip
                rows={below}
                value={(c) => c.vsExpected!}
                domain={[1 / 6, 6]}
                ranks={expectedRanks}
                format={fmtTimes}
                focus={focusCountry.iso3}
                onSelect={select}
                reference={{ value: 1, label: "As predicted" }}
                tone="below"
              />
            </div>
          </div>
          <p className="footnote">
            The prediction uses {regression.n} countries with population and GDP from the same recent year. Countries
            without recent GDP, including several microstates, Taiwan and the Holy See, are not part of it.
          </p>
        </section>

        <section id="over-time" className="section">
          <div className="section-head">
            <div>
              <h2>Month by month</h2>
              <p className="lede">
                {mode === "own"
                  ? "Each line is scaled to its own yearly average, set to 100, so the shape of the year is easy to compare across very different countries."
                  : "All lines share France's scale, so you can see how large the gaps between countries are. The vertical axis is logarithmic."}
              </p>
            </div>
            <Segmented
              value={mode}
              onChange={setMode}
              options={[
                { value: "own", label: "Shape of the year" },
                { value: "shared", label: "Actual levels" },
              ]}
            />
          </div>
          <CountryPicker
            countries={countries}
            picked={pickedCountries}
            onChange={(list) => setPicked(list.map((c: Country) => c.iso3))}
          />
          {pickedCountries.length ? (
            <MonthlyChart countries={pickedCountries} monthly={data.monthly} months={data.months} mode={mode} />
          ) : (
            <p className="empty">Add a country to see its monthly pattern.</p>
          )}
          <p className="footnote">
            A spike shows that searches rose, not why. Monthly values are built from weekly data, so weeks that span two
            months are split between them.
          </p>
        </section>

        <section id="all" className="section">
          <div className="section-head">
            <div>
              <h2>All countries</h2>
              <p className="lede">
                Sort by any column, search by name, or download the rows you see. Ranks count only the countries shown and
                are by search interest per resident.
              </p>
            </div>
          </div>
          <RankingsTable countries={countries} ranks={ranks} regions={regions} focus={focusCountry.iso3} onSelect={(iso) => {
            select(iso);
            document.getElementById("map")?.scrollIntoView({ behavior: "smooth" });
          }} />
        </section>

        <Method data={data} unranked={unranked} />
      </main>

      <footer className="footer">
        <p>
          Data collected {new Date(provenance.as_of).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}{" "}
          from {provenance.google_export_count} Google Trends comparisons and World Bank indicators. Search interest is a
          relative index, not a count of searches. These results are preliminary.
        </p>
      </footer>
    </>
  );
}

