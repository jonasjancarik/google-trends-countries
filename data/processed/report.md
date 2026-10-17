# Country attention: preliminary results

Study period: 2025-10-01 to 2026-09-30. Collection date: 2026-10-16.

## Available evidence

The dataset covers 193 UN member states and four separately identified entities:
the Holy See, Palestine, Taiwan and Kosovo. World Bank population data are available for
195 of 197 entities, GDP for 191,
and tourist arrivals for 120. Observation years accompany each value;
they need not match the search period. See `provenance.json` for exact requests and cache checksums.

Tourism observations in this snapshot refer to 2020.
They are historical context and cannot establish current tourism relationships.

Native browser exports cover 197 country topics in 76 comparisons.
These are original Google Trends measurements, not a third-party country-volume dataset.
The country-topic audit and original exports are documented in `docs/topic-audit.md` and `data/raw/trends/`.

Reviewed official supplements bring population coverage to 197 entities.

- TWN: 23,299,132 as of 2025-12-31; Year-end household-registered population. [Source](https://www.ris.gov.tw/info-liferay/app/channel/newsEnglishDetail/26245250). Registration-based year-end count; not a harmonized World Bank mid-year resident estimate. Includes Taiwan-administered territory; registration and residence can differ.
- VAT: 882 as of 2024-12-31; Year-end residents of Vatican City State, citizens and non-citizens. [Source](https://vaticanstate.va/en/state-and-government/general-informations/population.html). Vatican City residents correspond to the geographical Google topic used for the Holy See row; they are not the population of the Holy See as an institution. The observation predates the search window.

These denominators are not harmonized World Bank observations. Source, date and definition remain explicit in the country exports.

## Attention rankings

194 entities meet the complete, uncensored, sufficient-precision criteria.
This includes 190 UN members. Exclusions comprise 3 low-precision series, 0 incomplete or censored series, and 0 entities without population data.

Rankings apply only to that measured subset; missing countries may change the ordering.

Very small populations can produce large per-capita values. Regression-adjusted rankings provide a separate comparison.

### Top 20 among measured countries

| Country | Relative index per million residents |
| --- | ---: |
| Holy See | 2.88e+03 |
| Monaco | 98 |
| San Marino | 23.8 |
| Palau | 23 |
| Andorra | 21 |
| Liechtenstein | 19.6 |
| Tuvalu | 19.3 |
| Nauru | 19.1 |
| Iceland | 17.3 |
| Malta | 12.7 |
| Seychelles | 11.9 |
| Maldives | 8.36 |
| Bahamas | 7.46 |
| Barbados | 7.42 |
| Luxembourg | 7.27 |
| Dominica | 6.81 |
| Saint Kitts and Nevis | 6.59 |
| Singapore | 6.54 |
| Saint Lucia | 5.85 |
| New Zealand | 5.77 |

### Bottom 20 among measured countries

| Country | Relative index per million residents |
| --- | ---: |
| Chad | 0.0335 |
| Niger | 0.0371 |
| Burundi | 0.0383 |
| Ethiopia | 0.0388 |
| Central African Republic | 0.0398 |
| DR Congo | 0.0496 |
| China | 0.0641 |
| South Sudan | 0.0643 |
| Burkina Faso | 0.0702 |
| Madagascar | 0.0758 |
| Sierra Leone | 0.0763 |
| Mozambique | 0.0778 |
| Tanzania | 0.0806 |
| Angola | 0.0808 |
| Malawi | 0.0823 |
| Myanmar | 0.085 |
| Papua New Guinea | 0.0904 |
| Sudan | 0.0908 |
| Guinea | 0.0981 |
| Nigeria | 0.0982 |

The population-and-GDP log model uses 186 countries (in-sample R² for log attention = 0.887). It selects each country's latest common positive World Bank population/GDP year within the permitted three-year window, separately from per-capita denominators. The model_year, model_population and model_gdp_usd columns identify its inputs. Residuals measure attention relative to a geometric prediction; they do not explain its causes.

The largest positive adjusted residuals, expressed as multiples of the fitted prediction, are Afghanistan (3.84), Iran (3.79), Nepal (3.62), Tuvalu (3.16), Morocco (3.06).

The population/per-capita-attention Spearman correlation is -0.633. The population denominator can create an inverse association mechanically.

Across the 186 countries with both rankings, per-capita and regression-adjusted ranks have Spearman correlation 0.325.

Peak-month shares and ranks with each country's peak month removed are included for sensitivity analysis. A spike alone does not identify a news event.

The largest single-month contributions among eligible series are Côte d'Ivoire (30.9% of its annual index sum), Afghanistan (26.3% of its annual index sum), Argentina (25.8% of its annual index sum). These are concentration measures, not evidence of a particular cause.

## Interpreting the index

Audited country topics can include related terms in multiple languages and reduce name
ambiguity. Shared topics connect comparison batches to one reference scale. The resulting
annual measure is the equal-month mean of relative search shares, with the reference country's
mean set to 100. Dividing by population gives an index per million residents. Neither measure
is a count of searches or unique people. Topic assignment, sampling, rounding and Google
coverage remain sources of uncertainty.

Foreign attention per capita is unavailable: regional Trends scores use different search
bases and cannot be subtracted from the worldwide index. The official API's consistent
scaling also does not establish additive regional counts. Google Ads estimates cover keyword
sets and close variants rather than the same country-topic construct; they are not mixed in.

## Remaining uncertainty

Low-precision and censored series remain excluded, so the bottom 20 are the lowest among
eligible countries, not established as the least-searched countries in the full universe.
Use weaker, linked references where they can improve integer precision. A series whose own
peak reaches 100 while its baseline is suppressed cannot be repaired simply by changing the
other country in the comparison. Weekly bucket splitting also makes the monthly and annual
indices approximations.

Repeated independent exports and alternative reference paths are needed to assess ranking
stability before publication. The model's HC3 intervals omit Google sampling and calibration
uncertainty. See `docs/methodology.md`, `docs/topic-audit.md` and `docs/research.md` for definitions,
territorial qualifications and source links.

## Calculation sensitivity

60 adjacent pairs in the full eligible per-capita ranking differ by less than 1%. The scenario rank ranges in `ranking_sensitivity.csv` hold this cohort fixed. They are not sampling confidence intervals.

- median_high_precision_measurements: 11 ranks changed; maximum movement 2 places.
- equal_weight_calibration_links: 24 ranks changed; maximum movement 2 places.
- omit_COM_from_calibration_links: 0 ranks changed; maximum movement 0 places.
- omit_CZE_from_calibration_links: unavailable (Uncalibrated batches: ['browser-007', 'browser-008', 'browser-024', 'browser-026', 'browser-030', 'browser-031', 'browser-032', 'browser-034', 'browser-035', 'browser-036', 'browser-037', 'browser-039', 'browser-040', 'browser-043', 'browser-044', 'browser-045', 'browser-050', 'browser-051', 'browser-075']). This is a failed robustness check, not evidence of stability.
- omit_FJI_from_calibration_links: unavailable (Uncalibrated batches: ['browser-047', 'browser-056', 'browser-057', 'browser-059', 'browser-061', 'browser-074']). This is a failed robustness check, not evidence of stability.
- omit_FRA_from_calibration_links: unavailable (Uncalibrated batches: ['browser-001-france-czechia-paraguay-iraq-senegal', 'browser-002', 'browser-003', 'browser-004', 'browser-005', 'browser-006', 'browser-007', 'browser-008', 'browser-009', 'browser-010', 'browser-011', 'browser-012', 'browser-013', 'browser-014', 'browser-015', 'browser-016', 'browser-017', 'browser-018', 'browser-019', 'browser-020', 'browser-021', 'browser-022', 'browser-023', 'browser-024', 'browser-025', 'browser-026', 'browser-027', 'browser-028', 'browser-029', 'browser-030', 'browser-031', 'browser-032', 'browser-033', 'browser-034', 'browser-035', 'browser-036', 'browser-037', 'browser-038', 'browser-039', 'browser-040', 'browser-041', 'browser-042', 'browser-043', 'browser-044', 'browser-045', 'browser-046', 'browser-047', 'browser-048', 'browser-049', 'browser-050', 'browser-051', 'browser-052', 'browser-053', 'browser-054', 'browser-055', 'browser-056', 'browser-057', 'browser-058', 'browser-059', 'browser-060', 'browser-061', 'browser-062', 'browser-063', 'browser-064', 'browser-065', 'browser-066', 'browser-067', 'browser-068', 'browser-069', 'browser-070', 'browser-071', 'browser-072', 'browser-073', 'browser-074', 'browser-075']). This is a failed robustness check, not evidence of stability.
- omit_HTI_from_calibration_links: 0 ranks changed; maximum movement 0 places.
- omit_NRU_from_calibration_links: unavailable (Uncalibrated batches: ['browser-065', 'browser-067', 'browser-068', 'browser-071', 'browser-072']). This is a failed robustness check, not evidence of stability.

Annual rounding envelopes hold fitted calibration scales and population fixed. Low-score annual contributions use the same equal-month weighting as the primary index. These diagnostics do not justify admitting excluded countries; sampling, privacy noise, classification and calibration error remain unquantified. See `docs/methodology.md` for the rationale and repeated-panel protocol.
