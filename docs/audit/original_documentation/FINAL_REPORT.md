# Depression Remission Outcomes-Based Credit — Final MEPS-Based Valuation

**Completed October 28, 2026. Primary results in constant 2024 U.S. dollars.**

## Executive rate card

One fixed case rate per documented PHQ-2 remission proxy, at 100%, 75%, and 50% recognition. Each parenthetical range is a conditional 95% parameter-uncertainty interval. No provider-specific effectiveness or intervention costs enter the model.

| Payer population | 100% recognition (95% interval) | 75% recognition (95% interval) | 50% recognition (95% interval) |
|---|---:|---:|---:|
| All medical expenditures | $4,127 ($3,335 to $4,978) | $3,096 ($2,502 to $3,734) | $2,064 ($1,668 to $2,489) |
| Medicare | $5,200 ($4,005 to $6,467) | $3,900 ($3,004 to $4,851) | $2,600 ($2,002 to $3,234) |
| Medicaid | $1,978 ($1,282 to $2,703) | $1,483 ($961 to $2,027) | $989 ($641 to $1,352) |
| Private insurance | $1,926 ($1,211 to $2,664) | $1,444 ($908 to $1,998) | $963 ($605 to $1,332) |

## Conditional valuation breakeven probabilities

**Definition:** probability that the uncertainty-adjusted *modeled spontaneous-remission-discounted five-year valuation* is at least the proposed fixed credit. These are not the probabilities that an ACO, a provider, or Medicare will actually save money after making all payments. They are conditional on the model being structurally valid and the 53% discount being appropriate.

| Payer population | 100% credit | 75% credit | 50% credit |
|---|---:|---:|---:|
| All medical expenditures | 50.2% | 99.5% | 100.0% |
| Medicare | 50.1% | 98.4% | 100.0% |
| Medicaid | 50.3% | 91.8% | 99.8% |
| Private insurance | 50.0% | 90.6% | 99.6% |

**The approximately 50% result at full recognition is mechanical:** the proposed full price equals the model point estimate. It does *not* indicate that Medicare has a 50% chance of realizing net savings. Raising the discount improves these conditional model-risk percentages but cannot demonstrate causal impact.

## Empirical annual spending model

2019–2024 full-year MEPS annual expenditure files; 77,487 eligible adult person-years, including 6,604 PHQ-2-positive person-years. Two excluded person-year records had invalid geographic-region codes that created exact separation in the any-spending logistic equation; the final model has stable Hessian condition numbers. Expenditures are multiplied by 2024 / observation-year national CPI-U before modeling. Standardization weights reflect **current positive PHQ-2 screens within each payer population**, not all adults. Models predict outcomes at 2024 calendar-year levels.

| Payer population | Fit person-years | Current positive screens (target) | Remitted-screen state mean | Positive-screen state mean | Adjusted annual difference (95% survey CI) |
|---|---:|---:|---:|---:|---:|
| All medical expenditures | 77,487 | 6,604 | $9,456 | $16,202 | $6,746 ($5,517 to $7,975) |
| Medicare | 27,468 | 2,749 | $10,259 | $18,758 | $8,499 ($6,594 to $10,404) |
| Medicaid | 15,033 | 2,666 | $5,814 | $9,047 | $3,233 ($2,112 to $4,353) |
| Private insurance | 45,768 | 2,674 | $5,877 | $9,024 | $3,147 ($1,986 to $4,308) |

**Primary expenditure specification** (Maryland model): probability of any spending via survey-weighted logistic regression and mean positive expenditures via survey-weighted Gamma GLM with log link; controls for age and age squared, sex, race, poverty, education, insurance type, census region and year plus depressive-symptom state. No additional physical comorbidities. Survey-standardized predictions use the positive-screen target covariate distribution and stratified PSU influence-function variance.

## Five-year value beginning *after* the twelve-month remission assessment

The 12 months between the positive baseline screen and follow-up remission are **not valued**. From the remission documentation date, the model compares initially-remitted and initially-persistently-positive symptom states for five subsequent annual intervals. Allow later symptom remission and recurrence in both scenarios. Observed long-panel rates are P(positive next year | currently positive) = **48.84%** and P(positive next year | documented prior-positive then negative) = **23.74%**, based on 4,496 complete four-wave adults. The discounted difference in positive-state exposure is **1.30178 annual state-years** over five subsequent years (3% annual real discount, mid-year payment convention).

Formula for a payer-specific credit: **Adjusted annual state-spending difference × 1.30178 × (1 − 0.53) × CMS recognition share**. This is a model-based standardized price, not a treatment-effect estimate. The 53% spontaneous-remission rate is from Whiteford et al. (2013), a systematic review of untreated major depression among primary care adults. It is fixed for these conditional estimates rather than estimated from MEPS.

## Empirical and numerical validation

- All four primary two-part regressions converged. The complete-data, full-design PSU variance uses 395 PSUs in 105 strata (290 design degrees of freedom); all four primary models are full rank. Two invalid-region person-year records (both without positive depressive screen) were excluded to remove logistic separation rather than ignore a near-singular Hessian.

- Analytic gradients of both components of marginal standardization were independently checked against numerical finite differences. Matrix-based Markov propagation replicated the closed-form five-year factor, and 25 randomized transition matrices passed a second independent implementation.

- The 75% and 50% case rates and interval endpoints were checked against exact scaling of the 100% estimates. No negative payment amounts and no payer sums are constructed; insurance-covered domains overlap.

- A different mean estimator, Poisson pseudo-maximum likelihood with a log link (PPML), was fitted on the same covariates as an appendix-only check, never used to select the headline. Annual estimates are:

| Payer | Primary two-part | Independent PPML check |
|---|---:|---:|
| All medical expenditures | $6,746 | $7,222 |
| Medicare | $8,499 | $8,071 |
| Medicaid | $3,233 | $3,345 |
| Private insurance | $3,147 | $3,064 |

- Standard two-year MEPS panel records provided 2,430 positive-screen longitudinal pairs (weighted positive-to-positive transition rate **46.35%**), consistent in magnitude with the four-year panel **48.84%** persistence estimate. The four-year data supply the additional *formerly-positive/remitted* recurrence transitions that two-year panels cannot measure.

## Scope limitations material to CMS

1. **Clinical construct:** PHQ-2 changing from ≥3 to below 3 at an approximately annual observation is only a proxy; it is *not* the exact CMS Quality ID #370 outcome, which requires diagnosed depression plus PHQ-9 >9 at index and PHQ-9 <5 at 12 months ±60 days. The MEPS annual data lack the required PHQ-9 and precise measurement timestamps.

2. **Postremission association, not direct causal effect:** Annual MEPS health-state spending includes currently PHQ-2-negative individuals who may never have had depression. The primary model standardizes their predicted cost to baseline screen-positive covariates but cannot directly measure the costs of the actual *remitted* subgroup five years later. Prospective four-year remission-specific comparison remains imprecise, including a negative Medicare annual adjusted association; this discrepancy cannot be resolved by choosing the larger, positive estimate.

3. **Projected horizon:** The five-year period is extrapolated beyond available individual follow-up, under a stationary two-state Markov model. Transition dates within years, death, structural persistence, and changes in real cost are not separately modeled. Mid-year discounted annual beginning-of-year state rewards may overstate savings if symptoms recur early within a year.

4. **Financial meaning:** Medicare-paid expenditures among MEPS civilians are not the same as Medicare fee-for-service payment-standardized Part A/B/D claims, nor Medicare program savings net of intervention costs. Intervention expenses prior to documented remission are outside this valuation by design; unknown maintenance interventions during the future years cannot be identified separately.

5. **Conditional uncertainty:** The 95% ranges include sampling variation and modeled remission/recurrent screen transitions, but exclude uncertainty in the 53% spontaneous-remission assumption, PHQ-2 proxy validity, confounding, choice of extrapolation model and dependence between annual and four-year sample estimates. Near-50% breakeven at 100% recognition is a mathematical consequence, not evidence of actual financial breakeven.

## Actuarial status

**The table is a complete provisional MEPS-based NPVoC rate card under the agreed formula. It is not sufficient evidence to assert the published amounts are realized or causally attributable Medicare savings, nor exact Quality ID #370 clinical-remission values.** The principal unresolved limitation is identifying *post-remission* savings rather than extrapolating a cross-sectional symptom-state spending contrast. The independent PPML check improves confidence in the annual expenditure association but does not resolve that underlying estimand gap.

## References

- Maryland Diabetes Incidence Outcomes-Based Credit (approved May 2, 2019): https://hscrc.maryland.gov/Documents/Modernization/OBC/Maryland%20Diabetes%20Incidence%20Outcome-Based%20Credit%20Methodology%20-%20approved.pdf

- CMS 2026 MIPS Quality ID #370 (PHQ-9 definition): https://qpp.cms.gov/docs/QPP_quality_measure_specifications/CQM-Measures/2026_Measure_370_MIPSCQM.pdf

- Whiteford et al. 2013, untreated depression remission meta-analysis: https://pubmed.ncbi.nlm.nih.gov/22883473/

- BLS annual CPI-U values, national: https://www.bls.gov/regions/mid-atlantic/data/consumerpriceindexannualandsemiannual_table.htm
