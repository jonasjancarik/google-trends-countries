import { geoEqualEarth, geoPath } from "d3-geo";
import { useMemo, useState } from "react";
import { feature } from "topojson-client";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { GeometryCollection, Topology } from "topojson-specification";
import { SMALL_STATES, type Country } from "../data";
import { useWidth, type Hover } from "../hooks";
import { fillFor, type MapMetric } from "../scales";
import { CountryTooltip } from "./Tooltip";

type Props = {
  world: Topology;
  inView: Map<string, Country>;
  metric: MapMetric;
  ranks: Map<string, number>;
  focus: string | null;
  onSelect: (iso3: string) => void;
};

export function WorldMap({ world, inView, metric, ranks, focus, onSelect }: Props) {
  const [ref, width] = useWidth<HTMLDivElement>(900);
  const [hover, setHover] = useState<Hover<string>>(null);

  const shapes = useMemo(() => {
    const collection = feature(
      world,
      world.objects.countries as GeometryCollection,
    ) as FeatureCollection<Geometry, { ct?: number[] }>;
    return collection.features.filter((f) => f.id !== "ATA") as Feature<Geometry>[];
  }, [world]);

  const height = Math.round(width * 0.47);
  const { path, project } = useMemo(() => {
    const projection = geoEqualEarth().fitExtent(
      [
        [4, 4],
        [width - 4, height - 4],
      ],
      { type: "FeatureCollection", features: shapes },
    );
    return { path: geoPath(projection), project: projection };
  }, [shapes, width, height]);

  const dots = Object.entries(SMALL_STATES)
    .filter(([iso]) => inView.has(iso))
    .map(([iso, lonLat]) => ({ iso, point: project(lonLat)! }));

  const move = (iso: string) => (event: React.PointerEvent) => {
    const box = ref.current!.getBoundingClientRect();
    setHover({ item: iso, x: event.clientX - box.left, y: event.clientY - box.top });
  };

  const hovered = hover ? inView.get(hover.item) : undefined;
  const focusShapes = focus ? shapes.filter((s) => s.id === focus) : [];
  const focusDot = dots.find((d) => d.iso === focus);

  return (
    <div className="map" ref={ref} onPointerLeave={() => setHover(null)}>
      <svg width={width} height={height} role="img" aria-label="World map of search interest">
        <defs>
          <pattern id="nodata-hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="5" height="5" className="hatch-bg" />
            <line x1="0" y1="0" x2="0" y2="5" className="hatch-line" />
          </pattern>
        </defs>
        {shapes.map((shape, index) => {
          const iso = String(shape.id);
          const country = inView.get(iso);
          return (
            <path
              key={index}
              d={path(shape) ?? undefined}
              style={{ fill: fillFor(country, metric) }}
              className={country ? "map-country" : "map-country is-empty"}
              onPointerMove={country ? move(iso) : undefined}
              onClick={country ? () => onSelect(iso) : undefined}
            />
          );
        })}
        {focusShapes.map((shape, index) => (
          <path key={`focus${index}`} className="map-focus" d={path(shape) ?? undefined} />
        ))}
        {dots.map(({ iso, point }) => (
          <g key={iso} onPointerMove={move(iso)} onClick={() => onSelect(iso)} className="map-dot">
            <circle cx={point[0]} cy={point[1]} r={10} fill="transparent" />
            <circle
              cx={point[0]}
              cy={point[1]}
              r={4.5}
              style={{ fill: fillFor(inView.get(iso), metric) }}
              className="map-dot-mark"
            />
          </g>
        ))}
        {focusDot && (
          <circle className="map-focus" cx={focusDot.point[0]} cy={focusDot.point[1]} r={7.5} />
        )}
      </svg>
      {hover && hovered && (
        <CountryTooltip country={hovered} rank={ranks.get(hovered.iso3)} x={hover.x} y={hover.y} bounds={width} />
      )}
    </div>
  );
}
