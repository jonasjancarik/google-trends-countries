import { useState } from "react";
import type { Country } from "../data";
import { SERIES } from "../scales";

export function CountryPicker({
  countries,
  picked,
  onChange,
}: {
  countries: Country[];
  picked: Country[];
  onChange: (list: Country[]) => void;
}) {
  const [draft, setDraft] = useState("");
  const options = countries.filter((c) => c.eligible && !picked.includes(c)).sort((a, b) => a.country.localeCompare(b.country));

  const add = (name: string) => {
    const match = options.find((c) => c.country.toLowerCase() === name.trim().toLowerCase() || c.iso3 === name.trim().toUpperCase());
    if (!match) return;
    onChange([...picked, match].slice(-4));
    setDraft("");
  };

  return (
    <div className="picker">
      {picked.map((c, i) => (
        <span key={c.iso3} className="chip">
          <span className="key-dot" style={{ background: SERIES[i] }} />
          {c.country}
          <button type="button" aria-label={`Remove ${c.country}`} onClick={() => onChange(picked.filter((p) => p !== c))}>
            ×
          </button>
        </span>
      ))}
      {picked.length < 4 && (
        <form
          className="picker-add"
          onSubmit={(event) => {
            event.preventDefault();
            add(draft);
          }}
        >
          <input
            list="picker-countries"
            value={draft}
            placeholder="Add a country"
            aria-label="Add a country to compare"
            onChange={(event) => {
              setDraft(event.target.value);
              if (options.some((c) => c.country === event.target.value)) add(event.target.value);
            }}
          />
          <datalist id="picker-countries">
            {options.map((c) => (
              <option key={c.iso3} value={c.country} />
            ))}
          </datalist>
        </form>
      )}
      <span className="picker-hint">Up to four countries</span>
    </div>
  );
}
