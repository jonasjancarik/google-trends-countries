# Country-topic audit

Reviewed 16 October 2026. Read this before changing a country identifier or interpreting territorial coverage.

The measurements come from original Google Trends **Interest over time** CSV exports obtained through the normal browser interface. Every comparison uses Worldwide, all categories, Web Search and the fixed window 1 October 2025–30 September 2026. Country names and entity classifications were inspected in the selected comparison cards before import. The manifests under `config/browser-batches/` preserve each topic ID, exact CSV header, source URL, retrieval time and verification note; the original CSV bytes and checksums are under `data/raw/trends/`.

Candidate identifiers came from the published [G-TAB country/city list](https://github.com/epfl-dlab/GoogleTrendsAnchorBank/blob/db69456f4a8312639c6d7bd6229cab7edb543310/gtab/data/550_cities_and_countries.txt) and the [KG-BERT Freebase name/description mapping](https://github.com/yao8839836/kg-bert/tree/f3f260309c5e2986467a66e0e68fa7f53b1a150e/data/FB15K). These historical mappings were discovery aids, not search measurements or automatic verification. Their source files are cached in `data/raw/entity_candidates/`. Ambiguous matches were resolved in Google autocomplete and the resulting comparison cards.

| Entity | Rejected candidate or interpretation | Accepted topic |
| --- | --- | --- |
| Georgia | `/m/0d0x8`, US state | `/m/0d0kn`, Country |
| Italy | `/m/032xky`, “It”; an ISO-like name match to a different concept | `/m/03rjj`, Italy, Country in Europe |
| Brazil | `/m/0jwmp`, film | `/m/015fr`, Country in South America |
| Australia | `/m/026qnh6`, film | `/m/0chghy`, Country in Oceania |
| Ireland | `/m/012wgb`, the island | `/m/03rt9`, the country |
| Netherlands | `/m/049nq`, the broader Kingdom | `/m/059j2`, Country in Europe |
| Denmark | `/m/0k6nt`, legacy generic topic | `/g/121p5z1h`, current Country in Europe autocomplete choice |
| São Tomé and Príncipe | Search term, currency, football team, or similarly named generic topic | `/m/0j681`, Country in Central Africa |

## Generic topic labels

Google displays **Topic**, rather than Country, for Taiwan and Palestine. They are entity topics, not English search terms. The original UI classification is retained in their manifests; it is not relabeled as Country.

Taiwan's primary autocomplete result is `/m/06f32`. The preserved Freebase description identifies it with the Republic of China and its governed territory. It is included as an additional entity. World Bank population is unavailable; its per-capita ranking now uses the official year-end household-registered population, with its definition and territorial qualification recorded in the [methodology](methodology.md#economic-denominators-and-model).

Searching “State of Palestine” selects `/m/01k0p4`, displayed as Palestine, Topic. This identifier was independently matched to the [Palestinian-state Wikidata entity](https://www.wikidata.org/wiki/Q219060), whose Freebase identifier is `/m/01k0p4`. It is not the Mandatory Palestine identifier `/m/0h44w`. The World Bank denominator is its West Bank and Gaza series; topic coverage and statistical territorial coverage cannot be assumed identical. Palestine remains identified as a UN observer, outside the default UN-member view.

## Additional coverage qualifications

The VAT row is named Holy See in the UN-oriented universe; its measured geographical country topic is Vatican City (`/m/07ytt`, displayed as Country in Europe). The Holy See as an institution and Vatican City as a territory are distinct. Its per-capita index now uses the Governorate's 882 residents inside Vatican City at 31 December 2024, including citizens and non-citizens. This denominator does not count the Holy See as an institution or citizens living abroad. Its very small size drives the extended ranking's highest value. Kosovo uses the project convention XK/XKX and remains an additional entity rather than a UN member. The country classifications in Google do not determine the project's membership policy.

A country topic can contain related searches about sport, tourism, politics and culture. Its proprietary coverage is not an exhaustive, observable set of all searches concerning the territory. Entity review reduces obvious name collisions; it does not establish perfect classification.

## Calendar interpretation

Native weekly CSVs contain calendar dates and do not identify a source time zone. The manifests use Europe/Prague as the common **study-calendar interpretation**, not as a claim that the export discloses Google's server time zone. All comparisons were made in the same browser with the same date settings. Weekly buckets crossing month or study-window edges are split by covered days. Their within-week search shares are unknown, so monthly values and the twelve-month aggregate are approximations; clipping a bucket cannot recover its daily values.
