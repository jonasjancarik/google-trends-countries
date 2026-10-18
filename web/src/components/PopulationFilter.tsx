import type { Country } from "../data";
import { fmtPeople } from "../format";
import { useWidth } from "../hooks";

const SLIDER_STEPS = 1000;
const BIN_COUNT = 24;

type Props = {
  countries: Country[];
  minimumMillions: number;
  maximumMillions: number | null;
  onChange: (minimumMillions: number, maximumMillions: number | null) => void;
};

const cutoffForStep = (step: number, min: number, max: number) =>
  step === 0 ? 0 : step === SLIDER_STEPS ? max : min * (max / min) ** ((step - 1) / (SLIDER_STEPS - 1));

const stepForCutoff = (value: number, min: number, max: number) =>
  value <= 0 ? 0 : max === min ? SLIDER_STEPS : Math.min(
    SLIDER_STEPS,
    Math.max(1, Math.round(1 + (SLIDER_STEPS - 1) * Math.log(value / min) / Math.log(max / min))),
  );

const formatPopulation = (millions: number) => fmtPeople(millions * 1_000_000);

export function PopulationFilter({ countries, minimumMillions, maximumMillions, onChange }: Props) {
  const [ref, width] = useWidth<HTMLDivElement>(720);
  const values = countries
    .map((country) => country.population)
    .filter((population): population is number => population !== null && population > 0)
    .map((population) => population / 1_000_000);
  if (values.length === 0) {
    return <p className="empty">No ranked countries have a population value to show.</p>;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const minimumStep = stepForCutoff(minimumMillions, min, max);
  const maximumStep = maximumMillions === null ? SLIDER_STEPS : stepForCutoff(maximumMillions, min, max);
  const matching = values.filter((population) => population >= minimumMillions
    && (maximumMillions === null || population <= maximumMillions)).length;
  const minimumLabel = minimumMillions === 0 ? "No minimum" : `${formatPopulation(minimumMillions)} residents`;
  const maximumLabel = maximumMillions === null ? "No maximum" : `${formatPopulation(maximumMillions)} residents`;
  const rangeLabel = minimumMillions === 0
    ? maximumMillions === null ? "All populations" : `Up to ${formatPopulation(maximumMillions)} residents`
    : maximumMillions === null ? `At least ${formatPopulation(minimumMillions)} residents`
      : `${formatPopulation(minimumMillions)} – ${formatPopulation(maximumMillions)} residents`;
  const logMin = Math.log(min);
  const logSpan = Math.log(max) - logMin || 1;
  const xFor = (population: number) => ((Math.log(population) - logMin) / logSpan) * width;
  const bins = Array.from({ length: BIN_COUNT }, () => 0);
  for (const population of values) {
    const bin = Math.min(BIN_COUNT - 1, Math.floor(((Math.log(population) - logMin) / logSpan) * BIN_COUNT));
    bins[bin] += 1;
  }
  const maxBin = Math.max(1, ...bins);
  const minimumX = Math.max(0, Math.min(width, minimumMillions <= 0 ? 0 : xFor(minimumMillions)));
  const maximumX = Math.max(0, Math.min(width, maximumMillions === null ? width
    : maximumMillions <= 0 ? 0 : xFor(maximumMillions)));
  const ticks = [min, ...[1, 10, 100, 1000].filter((tick) => tick > min && tick < max)];
  const lastTick = ticks.at(-1)!;
  if (max / lastTick > 1.8) ticks.push(max);

  return (
    <div className="population-filter" ref={ref}>
      <div className="population-filter-heading">
        <div>
          <h3>Population range</h3>
          <p>Drag either end to filter both rankings.</p>
        </div>
        <output className="population-filter-value" htmlFor="minimum-residents maximum-residents">
          {rangeLabel}
        </output>
      </div>
      <svg
        className="population-histogram"
        viewBox={`0 0 ${width} 76`}
        role="img"
        aria-label={`Population distribution for ${values.length} ranked countries on a logarithmic scale. ${rangeLabel}.`}
      >
        <title>Residents among ranked countries</title>
        <desc>Each bar counts ranked countries in a logarithmically spaced population range. The vertical lines mark the minimum and maximum population.</desc>
        {bins.map((count, index) => {
          const left = (index / BIN_COUNT) * width;
          const binWidth = width / BIN_COUNT;
          const height = (count / maxBin) * 42;
          return (
            <rect
              key={index}
              className="population-bar"
              x={left + 2}
              y={48 - height}
              width={Math.max(1, binWidth - 4)}
              height={height}
              rx="2"
            >
              <title>{`${count} ranked ${count === 1 ? "country" : "countries"}`}</title>
            </rect>
          );
        })}
        <rect className="population-excluded" x="0" y="0" width={minimumX} height="50" />
        <rect className="population-excluded" x={maximumX} y="0" width={width - maximumX} height="50" />
        {minimumMillions > 0 && <line className="population-cutoff" x1={minimumX} x2={minimumX} y1="4" y2="50" />}
        {maximumMillions !== null && <line className="population-cutoff" x1={maximumX} x2={maximumX} y1="4" y2="50" />}
        <line className="population-axis" x1="0" x2={width} y1="50" y2="50" />
        {ticks.map((tick) => (
          <text key={tick} className="population-tick" x={xFor(tick)} y="69" textAnchor={tick === min ? "start" : tick === max ? "end" : "middle"}>
            {formatPopulation(tick)}
          </text>
        ))}
      </svg>
      <div className="population-sliders" role="group" aria-label="Filter rankings by population">
        <div className="population-slider-track" aria-hidden="true">
          <span style={{ left: `${minimumStep / SLIDER_STEPS * 100}%`, right: `${100 - maximumStep / SLIDER_STEPS * 100}%` }} />
        </div>
        <input
          id="minimum-residents"
          type="range"
          min="0"
          max={SLIDER_STEPS}
          step="1"
          value={minimumStep}
          style={{ zIndex: minimumStep > SLIDER_STEPS / 2 ? 3 : 2 }}
          aria-label="Minimum population"
          aria-valuetext={minimumLabel}
          onChange={(event) => {
            const cutoff = cutoffForStep(Math.min(Number(event.target.value), maximumStep), min, max);
            onChange(Math.min(cutoff, maximumMillions ?? Infinity), maximumMillions);
          }}
        />
        <input
          id="maximum-residents"
          type="range"
          min="0"
          max={SLIDER_STEPS}
          step="1"
          value={maximumStep}
          aria-label="Maximum population"
          aria-valuetext={maximumLabel}
          onChange={(event) => {
            const step = Math.max(Number(event.target.value), minimumStep);
            onChange(minimumMillions, step === SLIDER_STEPS ? null
              : Math.max(minimumMillions, cutoffForStep(step, min, max)));
          }}
        />
      </div>
      <p className="population-filter-note" aria-live="polite">
        {matching} of {values.length} ranked countries shown. Ranks are recalculated within this group.
      </p>
    </div>
  );
}
