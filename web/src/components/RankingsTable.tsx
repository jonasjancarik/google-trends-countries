import { csvFormat } from "d3-dsv";
import { useMemo, useState } from "react";
import type { Country } from "../data";
import { fmtIndex, fmtMoneyShort, fmtPeople, fmtTimes } from "../format";

type Key = "rank" | "country" | "region" | "perMillion" | "attention" | "vsExpected" | "population" | "gdp";

type Props = {
  countries: Country[];
  ranks: Map<string, number>;
  regions: string[];
  focus: string | null;
  onSelect: (iso3: string) => void;
};

const COLUMNS: { key: Key; label: string; numeric?: boolean; hint?: string }[] = [
  { key: "rank", label: "Rank", numeric: true },
  { key: "country", label: "Country" },
  { key: "region", label: "Region" },
  { key: "perMillion", label: "Per million residents", numeric: true },
  { key: "attention", label: "Total (France = 100)", numeric: true },
  { key: "vsExpected", label: "Versus prediction", numeric: true, hint: "Actual search interest divided by what population and GDP predict" },
  { key: "population", label: "Population", numeric: true },
  { key: "gdp", label: "GDP", numeric: true },
];

export function RankingsTable({ countries, ranks, regions, focus, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("all");
  const [sort, setSort] = useState<{ key: Key; desc: boolean }>({ key: "rank", desc: false });
  const [expanded, setExpanded] = useState(false);

  const valueOf = (c: Country, key: Key): number | string | null => {
    switch (key) {
      case "rank":
        return ranks.get(c.iso3) ?? null;
      case "country":
        return c.country;
      case "region":
        return c.region;
      default:
        return c[key];
    }
  };

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return countries
      .filter((c) => region === "all" || c.region === region)
      .filter((c) => !q || c.country.toLowerCase().includes(q) || c.iso3.toLowerCase().includes(q))
      .sort((a, b) => {
        const va = valueOf(a, sort.key);
        const vb = valueOf(b, sort.key);
        if (va === null && vb === null) return a.country.localeCompare(b.country);
        if (va === null) return 1;
        if (vb === null) return -1;
        const order = typeof va === "string" ? va.localeCompare(vb as string) : (va as number) - (vb as number);
        return sort.desc ? -order : order;
      });
  }, [countries, query, region, sort, ranks]);

  const visible = expanded || query || region !== "all" ? rows : rows.slice(0, 25);

  const download = () => {
    const blob = new Blob([csvFormat(rows.map((c) => c.raw))], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "country-attention.csv";
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const toggleSort = (key: Key) =>
    setSort((s) =>
      s.key === key ? { key, desc: !s.desc } : { key, desc: !["rank", "country", "region"].includes(key) },
    );

  return (
    <div className="table-block">
      <div className="controls">
        <label className="field">
          <span>Find a country</span>
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Name or ISO code" />
        </label>
        <label className="field">
          <span>Region</span>
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="all">All regions</option>
            {regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="button" onClick={download}>
          Download {rows.length} rows as CSV
        </button>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={col.numeric ? "num" : undefined}
                  aria-sort={sort.key === col.key ? (sort.desc ? "descending" : "ascending") : "none"}
                  title={col.hint}
                >
                  <button type="button" onClick={() => toggleSort(col.key)}>
                    {col.label}
                    <span className="sort-mark" aria-hidden="true">
                      {sort.key === col.key ? (sort.desc ? "↓" : "↑") : ""}
                    </span>
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((c) => (
              <tr key={c.iso3} className={c.iso3 === focus ? "is-focus" : undefined} onClick={() => onSelect(c.iso3)}>
                <td className="num">{ranks.get(c.iso3) ?? "—"}</td>
                <td>
                  <span className="cell-country">{c.country}</span>
                  {!c.unMember && <span className="tag">{c.membership === "UN observer" ? "UN observer" : "Not a UN member"}</span>}
                </td>
                <td className="muted cell-region">{c.region}</td>
                <td className="num strong">{c.eligible ? fmtIndex(c.perMillion) : <span className="muted">Too few searches</span>}</td>
                <td className="num">{c.eligible ? fmtIndex(c.attention) : "—"}</td>
                <td className="num">{c.eligible ? fmtTimes(c.vsExpected) : "—"}</td>
                <td className="num">{fmtPeople(c.population)}</td>
                <td className="num">{fmtMoneyShort(c.gdp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {visible.length < rows.length && (
        <button type="button" className="button button-quiet show-all" onClick={() => setExpanded(true)}>
          Show all {rows.length} countries
        </button>
      )}
    </div>
  );
}
