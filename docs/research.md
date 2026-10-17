# Search-attention data availability

Checked 16 October 2026. Read this before choosing a search data source or interpreting the results.

## Measurement decision

A worldwide **relative country-topic attention index** is potentially measurable. An absolute count of all Google searches about each country is not available through the public Trends interface. Foreign attention per capita is not established by the available regional data. The delivered snapshot contains real demographic/economic observations and native browser exports for all 197 country topics. Per-capita rankings are published only where the precision and population rules pass.

The country is the **subject** of the query, not its origin. A table organized by the country where queries originated does not, by itself, measure worldwide attention to that country.

| Source | What it provides | Suitability and access |
| --- | --- | --- |
| Google Trends country topics | Sampled relative interest in concepts, with language variants grouped by Google | Best match to the intended subject, subject to auditing and calibration. Direct HTTP returned 429; the normal browser interface subsequently supplied the measured panel. |
| Official Google Trends API alpha | Consistent scaling across requests; daily, weekly, monthly and yearly aggregation; geographic restrictions | Preferred acquisition route if access is approved. The official page still requires an application. Consistent scaling does not turn its output into search counts. |
| Google Ads Keyword Planner | Approximate keyword search estimates, including historical months and close-variant grouping | Useful for a separately defined keyword study, but does not offer the same multilingual country-topic construct. Requires authorized Google Ads/OAuth/developer-token access. No credentials were supplied. |
| Trends public BigQuery dataset | Selected top and rising queries | Selection excludes most country-topic/month combinations. Not a complete country-volume panel. |
| Published international-attention studies | Historical country-to-country search networks and methods | Useful precedents; not a current trailing-year dataset with an established common volume scale. |
| GoogleTrendArchive | Trending Now surges over a historical interval | Measures selected bursts. Neither its location count nor a country's appearance in the archive supplies total worldwide country-topic interest. |

[Google's topic definition](https://support.google.com/trends/answer/4359550?hl=en) supports using concepts across languages. Topic coverage is not transparent or necessarily exhaustive; political entities must be reviewed in the interface, particularly Georgia, Chad, Jordan, Türkiye, the two Congos and the two Koreas. A plain country name is never automatically accepted as a topic.

The [official API page](https://developers.google.com/search/apis/trends) and [announcement](https://developers.google.com/search/blog/2025/07/trends-api) distinguish consistent scaling from absolute counts. The announcement describes five-term UI comparisons, while the current landing page says eight. The importer accepts up to eight; use the current interface's actual limit and record the original export.

[Keyword Planner historical metrics](https://developers.google.com/google-ads/api/docs/keyword-planning/generate-historical-metrics) describe approximate monthly volumes and keyword/close-variant behavior. A multilingual list of country names would need explicit language coverage, entity-disambiguation checks and de-duplication across variants. Adding translations without this work can double-count or change the target construct. [Google Ads access requirements](https://developers.google.com/google-ads/api/starter-checklist) also make this a credentialed route, not an anonymous substitute.

The [public BigQuery dataset description](https://support.google.com/trends/answer/12764470?hl=en) identifies top-25 selections. [GoogleTrendArchive](https://arxiv.org/abs/2603.21871) concerns Trending Now. Neither establishes the requested complete monthly panel. The focused source search found no public, current dataset that could support the requested rankings as defined; this is a search result, not proof that no such dataset exists.

## Research precedents

[West, *Calibration of Google Trends Time Series* (CIKM 2020)](https://arxiv.org/abs/2007.13861) introduces G-TAB: anchors spanning different popularity levels make cross-request calibration possible while reducing integer-rounding problems. A single very popular reference can suppress small-country signals. This project implements a simpler auditable graph of shared country topics, with explicit precision and consistency gates; it does not claim to reproduce G-TAB or inherit its empirical validation.

[*Googling the World: Global and Regional Information Flows in Google Trends* (2018)](https://ijoc.org/index.php/ijoc/article/view/7947) studies international country searches. [*What We Read, What We Search: Media Attention and Public Attention Among 193 Countries* (2018)](https://arxiv.org/abs/1802.06437) compares historical media and search networks. They establish a relevant literature, but their periods and regional measures cannot be reused as current absolute country search counts.

## Live access checks

A public suggestion lookup for France returned HTTP 200 but offered narrower or unrelated entities. No country mapping was accepted automatically. Wikidata Q142 supplied `/m/0f8l9c` as France's Freebase identifier, which was used only as a candidate in one worldwide Trends measurement probe for 1 October 2025–30 September 2026. That request returned `HTTP Error 429: unknown`. No measurement was obtained and no repeated requests, alternate identities or proxies were used. Receipts and source responses are in `data/raw/access_checks.json` and `data/raw/access_probes/`.

There is no documented public alpha endpoint contract available in the sources reviewed that can be implemented and tested without approved access. The project therefore imports audited public-interface CSV exports. An approved API adapter remains future work; no speculative endpoint or credential environment variable is presented as functional.

## Supporting data

The [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) supplies population, GDP, GDP per capita and optional tourist arrivals. Raw responses, pagination and download timestamps are cached. The [UN member roster](https://www.un.org/en/about-us/member-states) determines the 193-country core; [observer-state information](https://www.un.org/en/about-us/non-member-states) supports treating the Holy See and Palestine separately. Taiwan and Kosovo extend the dataset to 197 entities without changing the core UN scope.

## Browser collection result

The browser route succeeded where the initial direct request did not. It supplied 76 accepted Interest over time CSV comparisons covering all 197 entities for October 2025–September 2026. Country-topic identities were audited and shared references connected the series to a common scale. Completing the weaker-reference comparisons recovered 65 of the 68 entities previously excluded for measurement quality. Official population supplements subsequently added Taiwan and the Holy See/Vatican City row. The project publishes 194 per-capita rankings, including 190 UN members, and preserves explicit reasons for every exclusion. These remain relative indices; no absolute or foreign search counts were obtained.

An earlier page-display error persisted after one normal reload, so collection paused. A later normal visit to the same comparison succeeded, allowing all 17 pending batches and two final paired comparisons to be collected. The UI did not expose an HTTP status for the error; it remains recorded separately from the confirmed earlier HTTP 429. Further paired retries left Cabo Verde at 1–100, while Haiti and Comoros returned identical 4–100 exports. They still fail the minimum score of 5. Identical repeats are preserved as access checks without increasing calibration weight. No current, complete third-party country-volume dataset was adopted: the attention measurements come directly from Google's browser exports.

The population supplements come from [Taiwan's Ministry of the Interior](https://www.ris.gov.tw/info-liferay/app/channel/newsEnglishDetail/26245250) and the [Governorate of Vatican City State](https://vaticanstate.va/en/state-and-government/general-informations/population.html). Their year-end registration/residency definitions differ from the World Bank series; dates, source pages and qualifications are retained. This is an explicit extension of denominator coverage, not newly collected search attention. Neither entity has a GDP observation in this snapshot, so both remain outside the regression.
