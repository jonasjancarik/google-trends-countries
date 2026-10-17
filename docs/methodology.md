# Methodological note

Read this before comparing country scores, changing normalization, or publishing a ranking.

## Research population and time

The universe consists of the 193 UN members, the Holy See and Palestine as observers, and Taiwan and Kosovo as additional entities. Membership status remains a column; the web page defaults to UN members. Kosovo uses the user-assigned XK/XKX convention, not an officially assigned ISO 3166-1 code. Inclusion does not express a position on political status. Palestine joins to the World Bank's West Bank and Gaza series; this territorial definition must be considered when combining sources. World Bank region labels are used without reclassification.

The study uses the last twelve **complete calendar months** before the collection date in Europe/Prague. On 16 October 2026, that means 1 October 2025–30 September 2026. The current month is omitted. Google request geography is worldwide (`geo=""`), category is all categories (`0`), and property is Google Web Search (`""`). Source dates and retrieval times are recorded separately.

## Search construct

The target is interest in a country topic as classified by Google, across search origins. It is not search activity originating in that country, the country's entire cultural footprint, or every query mentioning one of its places, citizens or products. Country topics reduce language and homonym problems but cannot eliminate classification errors. Review the selected entity, its type and related searches. Reject a football team, US state, person, bird or food entity even when its label resembles the country's name.

Google's [normalization explanation](https://support.google.com/trends/answer/4365533?hl=en) describes relative interest and low-volume suppression. Let `q_it` denote the topic's share of Google searches worldwide in interval `t`. For batch `b`, the observed value is approximately `y_bit = c_b q_it`, rounded and potentially suppressed. The batch constant changes between independently exported comparisons. Thus a 60 from one export is not comparable to a 30 from another without calibration.

## Shared-reference calibration

The implemented estimator uses shared topic/interval observations. All batches must have the same source window, interval resolution, study-calendar interpretation, origin geography, category and search property. The native CSV supplies dates without a source time zone. Requests used the same browser/date settings; no sub-day timestamps are inferred. See the topic audit note for this limitation. A country must retain one topic ID. Duplicate rows and conflicting topic identities fail validation.

For two batches sharing topics, estimate `d_ab = median(log(y_ait) - log(y_bit))` over identical intervals where both values are at least 5. Require six usable overlapping topic-interval observations. Six is a pragmatic validation threshold, not a statistical guarantee. The 90th percentile absolute log deviation must not exceed 0.2. This corresponds to approximately 22% multiplicative disagreement and is a quality gate, not a confidence interval.

Solve weighted least squares for `log(k_b) - log(k_a) = d_ab`, weighting each batch link by its usable overlap count and fixing one root scale. All batches must connect to the reference country. Reject a disconnected graph or a fitted link residual above 0.2. Linked weaker country topics can bridge comparisons that would round small countries to zero beside a large reference. The current implementation requires those bridge exports to be supplied; it does not construct an anchor bank automatically.

Multiply each observation by its fitted batch scale. Shared topics are repeated measurements, never additional traffic. For a country/interval present more than once, retain the observation with the highest original score to reduce integer-rounding error; alphabetical batch ID breaks ties. This can introduce selection effects and is not an uncertainty estimate. Repeated-export stability analysis and alternative reference paths are required before publication. The procedure is inspired by [G-TAB](https://arxiv.org/abs/2007.13861), but is deliberately simpler. Its empirical measurement accuracy and sampling stability have not been independently established.

## Monthly and annual indices

Monthly exports are used directly. Daily or weekly interval means are weighted by the number of covered calendar days in each month. Splitting a week across months assumes constant search share within that week, so the output is a monthly approximation. Partial or missing coverage is not extrapolated. A month containing a suppressed value (`0` or `<1`) stays missing, rather than acquiring an invented zero-search count.

Scale the reference country's mean over the twelve complete months to 100. Define `S_i* = (1/12) Σ_t I_it`, the equal-month mean of the calibrated relative search-share series. This is an annual **relative attention index**, not a sum of searches. It weights calendar months equally; daily weights are used within months. Search totals vary over time, and their monthly denominators are unknown, so this cannot recover annual query counts. A choice to weight months by days would define a different index.

The principal per-capita measure is `A_i* = 10^6 S_i* / P_i`, labeled **relative attention index per million residents**. Values depend on the reference scale; ordering does not depend on an arbitrary common multiplier. Country topics may overlap, so country indices are not assumed to sum to a share of all searches about countries.

Rankings require all twelve monthly values, no suppressed intervals and no accepted interval with an original score below 5. This conservative rule can exclude small countries and bias the measured subset. Their status is retained and they are not interpreted as the least-searched countries. A country without population may have a total relative index but has no per-capita rank. Ties share the minimum rank. Top/bottom lists contain up to twenty eligible entities; at fewer than forty measured entities they can overlap, and always refer only to the measured subset.

## Foreign attention

`(S_i - D_i)/P_i` requires compatible worldwide and domestic counts, or documented weights that transform origin-specific measures into the same additive count basis. Regional Trends popularity indices do not satisfy that condition. Even an API with consistent scaling does not establish regional additivity. The project keeps absolute counts and foreign attention missing; a guarded calculation helper rejects regional-index input. No regional subtraction is performed.

## Economic denominators and model

Use World Bank indicators `SP.POP.TOTL`, `NY.GDP.MKTP.CD`, `NY.GDP.PCAP.CD` and optional `ST.INT.ARVL`, source 2. For each indicator/entity, select the latest positive observation in the six-year interval ending at the fixed economic reference year, defaulting to the year before the search window ends. Save every observation year and the full downloaded history. Population is not projected forward to the search year. This creates a timing limitation, especially for fast-changing or displaced populations.

For Taiwan and the Holy See, which lack World Bank population, this snapshot now uses two explicitly reviewed official supplements. This extends the original World Bank-only denominator policy; it does not change any search-quality rule.

| Entity | Population and observation date | Definition and source |
| --- | ---: | --- |
| Taiwan | 23,299,132; 31 December 2025 | Household-registered population, [Taiwan Ministry of the Interior](https://www.ris.gov.tw/info-liferay/app/channel/newsEnglishDetail/26245250) |
| Holy See row / Vatican City topic | 882; 31 December 2024 | Residents inside Vatican City State, including citizens and non-citizens, [Governorate of Vatican City State](https://vaticanstate.va/en/state-and-government/general-informations/population.html) |

These year-end observations are not harmonized World Bank population estimates. Registration and residence can differ in Taiwan. Vatican City's residents are not a population count of the Holy See as an institution; they match the geographical topic used in this row. Its exceptionally small denominator puts it first in the extended per-capita ranking. The web page still defaults to UN members.

The reviewed manifest and original HTML are cached under `data/raw/population_supplements/`. The rebuild verifies source checksums, reviewed status, unique known entities, positive integer counts and dates inside the same six-year economic window. A supplement cannot replace an existing World Bank population. `population_source`, `population_source_url`, `population_as_of`, `population_definition` and `population_note` accompany the country exports, and the full records enter provenance. GDP remains missing for these two entities, so they do not enter the population-and-GDP regression.

Fit `log(S_i*) = α + β log(P_i) + γ log(GDP_i) + ε_i` using at least ten eligible countries. Population and GDP must refer to the same year, no more than two years before the economic reference year. Report exclusions, sample size, coefficients, R², HC3 standard errors/95% intervals, condition number, leverage and Cook's distance. Population and total GDP can be correlated; coefficient interpretations are conditional and should not be treated as causal.

The residual is `R_i = log(S_i*) - fitted_log(S_i*)`; `exp(R_i)` is attention relative to the fitted geometric prediction. This is not an arithmetic conditional mean or a predicted count. Changing the overall search-index scale changes only the intercept. Compare adjusted and per-capita ranks using Spearman correlation. Other correlations, region distributions and tourism comparisons are descriptive; observation years can differ and missing tourism coverage is substantial. No significance-based causal claim is made.

Indicator correlations require observations no more than two years before the economic reference year. All available tourism observations in the delivered snapshot are from 2020 and are therefore excluded from these correlations. They remain available as historical context in the exports.

Inspect the association of population with per-capita attention, remembering that population occurs in the denominator. Save each country's peak-month share and recompute per-capita ranks after removing its highest month. This is an event-sensitivity diagnostic: it does not identify a news event. External contemporaneous evidence is needed before attributing a spike to a particular event.

## Limits on publication

The delivered panel contains 76 native Google Trends comparison exports covering all 197 entities and publishes per-capita ranks for 194 eligible entities, including the two official population supplements. The country identities were reviewed and the full comparison graph passes calibration checks. Tests on synthetic fixtures establish implementation behavior; they do not establish sampling stability or empirical ranking accuracy. Cabo Verde, Comoros and Haiti remain excluded for low integer precision. Before publication, audit topics and territorial coverage, collect repeated samples, examine alternate anchors and missing-country selection, and quantify the resulting rank sensitivity. Do not add unsupported precision or reinterpret this exploratory index as absolute attention.

Browser-refinement references were chosen from observed series peaks, using a known topic with lower measured search interest where practical. Removing other strong topics from the batch can also improve the scale available to a target. This changes measurement precision, not the underlying definition of attention. No value was inferred from population, GDP, neighboring countries or a different search platform. After the refinements, Cabo Verde's original-score range is 1–100; Comoros and Haiti each have a paired export ranging from 4–100. Their own peaks already use the top of the scale, so merely weakening the other topic cannot remove the remaining whole-window rounding limitation. Their primary per-capita ranks are withheld. Repeated exports can differ because Google samples searches; the current panel does not estimate that sampling distribution.

A subsequent retry downloaded paired comparisons for all three. Cabo Verde remained at 1–100; Haiti and Comoros returned byte-identical CSVs to the previous paired exports. The new Cabo Verde comparison is `browser-075`. Identical repeats were recorded under `data/raw/followup_checks/2026-10-16/` and were not added to the calibration graph or treated as independent sampling evidence. Collecting shorter windows would require a separately validated method for linking resolutions and windows; the current estimator requires matching windows and resolution, so those fragments are not combined into the published annual index.
