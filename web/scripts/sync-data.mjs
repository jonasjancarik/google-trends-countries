// Copies the pipeline's processed outputs into public/data so the page can load them.
// Run automatically before `dev` and `build`; rebuild the dataset first with the Python CLI.
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const target = join(root, "web", "public", "data");
const files = [
  ["data/processed/rankings.csv", "rankings.csv"],
  ["data/processed/monthly_attention.csv", "monthly_attention.csv"],
  ["data/processed/regression.json", "regression.json"],
  ["data/processed/diagnostics.json", "diagnostics.json"],
  ["data/processed/provenance.json", "provenance.json"],
  ["data/processed/ranking_sensitivity.csv", "ranking_sensitivity.csv"],
  ["data/processed/sensitivity.json", "sensitivity.json"],
  ["docs/methodology.md", "methodology.md"],
  ["docs/collection.md", "collection.md"],
  ["static/world_110m.json", "world_110m.json"],
];

mkdirSync(target, { recursive: true });
const missing = files.filter(([source]) => !existsSync(join(root, source)));
if (missing.length) {
  console.error(
    `Missing ${missing.map(([s]) => s).join(", ")}.\n` +
      "Build the dataset first: uv run country-attention build --offline",
  );
  process.exit(1);
}
for (const [source, name] of files) copyFileSync(join(root, source), join(target, name));
const provenancePath = join(target, "provenance.json");
const provenance = JSON.parse(readFileSync(provenancePath, "utf8"));
const comparisonPath = join(root, "data/processed/panel_comparison.json");
provenance.repeat_panel_comparison_available = false;
if (existsSync(comparisonPath) && existsSync(join(root, "data/processed/panel_comparison.csv"))) {
  const comparison = JSON.parse(readFileSync(comparisonPath, "utf8"));
  const countriesHash = createHash("sha256").update(readFileSync(join(root, "data/processed/countries.csv"))).digest("hex");
  const primaryHashes = provenance.search_exports.map((path) =>
    JSON.parse(readFileSync(join(root, dirname(path), "receipt.json"), "utf8")).sha256,
  ).sort();
  if (comparison.window_start === provenance.window_start && comparison.window_end === provenance.window_end
      && comparison.primary_countries_sha256 === countriesHash
      && JSON.stringify(comparison.panels[0]?.export_sha256) === JSON.stringify([...new Set(primaryHashes)])) {
    for (const name of ["panel_comparison.csv", "panel_comparison.json"]) {
      copyFileSync(join(root, "data/processed", name), join(target, name));
    }
    provenance.repeat_panel_comparison_available = true;
  }
}
writeFileSync(provenancePath, JSON.stringify(provenance, null, 2) + "\n");
console.log(`Copied ${files.length} data files to web/public/data`);
