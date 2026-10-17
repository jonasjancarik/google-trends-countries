# Map geometry

`world_110m.json` is a cached Plotly world topology downloaded on 16 October 2026 from
https://cdn.plot.ly/un/world_110m.json. It provides map geometry only, not research observations.
`web/scripts/sync-data.mjs` copies it into the web page's data folder so the map does not require a live CDN request.
Small states and disputed territories may not have separate geometry at this resolution.
