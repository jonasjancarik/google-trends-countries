// Copies the pipeline's processed outputs into public/data so the page can load them.
// Run automatically before `dev` and `build`; rebuild the dataset first with the Python CLI.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
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
console.log(`Copied ${files.length} data files to web/public/data`);
