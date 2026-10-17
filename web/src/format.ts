const sig = (value: number, digits = 3) => {
  if (value === 0) return "0";
  const abs = Math.abs(value);
  if (abs >= 1000) return Math.round(value).toLocaleString("en-US");
  return Number(value.toPrecision(digits)).toLocaleString("en-US", { maximumFractionDigits: 6 });
};

export const fmtIndex = (value: number | null | undefined, digits = 3) =>
  value === null || value === undefined ? "—" : sig(value, digits);

export const fmtPeople = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "—";
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)} billion`;
  if (value >= 1e6) return `${sig(value / 1e6)} million`;
  if (value >= 1e4) return `${sig(value / 1e3)} thousand`;
  return Math.round(value).toLocaleString("en-US");
};

export const fmtMoney = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "—";
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)} trillion`;
  if (value >= 1e9) return `$${sig(value / 1e9)} billion`;
  if (value >= 1e6) return `$${sig(value / 1e6)} million`;
  return `$${Math.round(value).toLocaleString("en-US")}`;
};

export const fmtTimes = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "—";
  return value >= 1 ? `${sig(value, 2)}×` : `${sig(1 / value, 2)}× less`;
};

export const fmtPercent = (value: number | null | undefined) =>
  value === null || value === undefined ? "—" : `${Math.round(value * 100)}%`;

export const fmtMonth = (month: string, style: "short" | "long" = "short") =>
  new Date(`${month}-01T00:00:00`).toLocaleDateString("en-GB", {
    month: style === "short" ? "short" : "long",
    year: style === "short" ? "2-digit" : "numeric",
  });

export const ordinal = (n: number) => {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`;
};

/** Tick values on a log scale: 1, 3, 10, 30 … between min and max. */
export function logTicks(min: number, max: number, steps: number[] = [1, 3]) {
  const ticks: number[] = [];
  for (let e = Math.floor(Math.log10(min)) - 1; e <= Math.ceil(Math.log10(max)); e++) {
    for (const s of steps) {
      const v = s * 10 ** e;
      if (v >= min * 0.999 && v <= max * 1.001) ticks.push(v);
    }
  }
  return ticks;
}

export const fmtTick = (value: number) => {
  if (value >= 1e12) return `${sig(value / 1e12)}T`;
  if (value >= 1e9) return `${sig(value / 1e9)}B`;
  if (value >= 1e6) return `${sig(value / 1e6)}M`;
  if (value >= 1e3) return `${sig(value / 1e3)}k`;
  return sig(value);
};

export const fmtMoneyShort = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "—";
  if (value >= 1e12) return `$${sig(value / 1e12)}T`;
  if (value >= 1e9) return `$${sig(value / 1e9)}B`;
  return `$${sig(value / 1e6)}M`;
};
