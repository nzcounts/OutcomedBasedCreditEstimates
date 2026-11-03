#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import pandas as pd,json,os
P=Path(__file__).resolve().parents[1]
R=Path(os.environ.get('MEPS_OUTPUT_DIR',str(P/'results'/'primary')))
credit=pd.read_csv(R/'FINAL_100_75_50_AND_BREAKEVEN.csv')
annual=pd.read_csv(R/'annual_primary_models.csv').set_index('payer')
val=pd.read_csv(R/'APPENDIX_independent_PPML.csv').set_index('payer')
summary=json.loads((R/'AUDIT.json').read_text())
N=['All medical expenditures','Medicare','Medicaid','Private insurance']

def dollars(x):
 return f'{"−" if x<0 else ""}${abs(x):,.0f}'
def pct(x):return f'{x:.1%}'
md=[]
md.append('# Depression Remission Outcomes-Based Credit — Final MEPS-Based Valuation\n')
md.append('**Completed October 28, 2026. Primary results in constant 2024 U.S. dollars.**\n')
md.append('## Executive rate card\n')
md.append('One model-based price per hypothetical remission scenario, at 100%, 75%, and 50% recognition. Each parenthetical range is a conditional 95% parameter-uncertainty interval. No provider-specific effectiveness or intervention costs enter the model.\n')
md.append('| Payer population | 100% recognition (95% interval) | 75% recognition (95% interval) | 50% recognition (95% interval) |')
md.append('|---|---:|---:|---:|')
for payer in N:
 r=credit[credit.payer==payer].set_index('recognition_pct')
 md.append('| '+payer+' | '+' | '.join(f'{dollars(r.loc[t,"nonnegative_payment_candidate_usd"])} ({dollars(r.loc[t,"95_interval_signed_credit_low_usd"])} to {dollars(r.loc[t,"95_interval_signed_credit_high_usd"])})' for t in [100,75,50])+' |')
md.append('\n## Conditional valuation breakeven probabilities\n')
md.append('**Definition:** probability that the uncertainty-adjusted *modeled spontaneous-remission-discounted five-year valuation* is at least the proposed fixed credit. These are not the probabilities that an ACO, a provider, or Medicare will actually save money after making all payments. They are conditional on the model being structurally valid and the 53% discount being appropriate.\n')
md.append('| Payer population | 100% credit | 75% credit | 50% credit |')
md.append('|---|---:|---:|---:|')
for payer in N:
 r=credit[credit.payer==payer].set_index('recognition_pct')
 md.append('| '+payer+' | '+' | '.join(pct(r.loc[t,'conditional_probability_valuation_exceeds_payment']) for t in [100,75,50])+' |')
md.append('\n**The approximately 50% result at full recognition is mechanical:** the proposed full price equals the model point estimate. It does *not* indicate that Medicare has a 50% chance of realizing net savings. Raising the discount improves these conditional model-risk percentages but cannot demonstrate causal impact.\n')
md.append('## Empirical annual spending model\n')
md.append('2019–2024 full-year MEPS annual expenditure files; 77,487 eligible adult person-years, including 6,604 PHQ-2-positive person-years. Two excluded person-year records had invalid geographic-region codes; the historical separation diagnostic is not available; the final model has stable Hessian condition numbers. Expenditures are multiplied by 2024 / observation-year national CPI-U before modeling. Standardization weights reflect **current positive PHQ-2 screens within each payer population**, not all adults. Models predict outcomes at 2024 calendar-year levels.\n')
md.append('| Payer population | Fit person-years | Current positive screens (target) | Negative-screen state mean | Positive-screen state mean | Adjusted annual difference (95% survey CI) |')
md.append('|---|---:|---:|---:|---:|---:|')
for payer in N:
 a=annual.loc[payer]
 lo=a['annual_diff_ci_low'];hi=a['annual_diff_ci_high']
 md.append(f'| {payer} | {int(a.n_model):,} | {int(a.n_index_screen_positive):,} | {dollars(a.annual_remitted_state_cost_2024usd)} | {dollars(a.annual_depression_positive_cost_2024usd)} | {dollars(a.annual_diff_positive_minus_negative_2024usd)} ({dollars(lo)} to {dollars(hi)}) |')
md.append('\n**Primary expenditure specification** (Maryland model): probability of any spending via survey-weighted logistic regression and mean positive expenditures via survey-weighted Gamma GLM with log link; controls for age and age squared, sex, race, poverty, education, insurance type, census region and year plus depressive-symptom state. No additional physical comorbidities. Survey-standardized predictions use the positive-screen target covariate distribution and stratified PSU influence-function variance.\n')
md.append('## Five-year value beginning *after* the twelve-month remission assessment\n')
md.append('The 12 months between the positive baseline screen and follow-up remission are **not valued**. From a hypothetical landmark, the model compares initially-negative and initially-positive symptom states for five subsequent annual intervals. Allow later symptom remission and recurrence in both scenarios. Observed long-panel rates are P(positive next year | currently positive) = **48.84%** and P(positive next year | documented prior-positive then negative) = **23.74%**, based on 4,496 complete four-wave adults. The negative-after-prior-positive state includes people beyond their first negative screen; 101 of 444 transition observations had already been negative in the preceding wave. The discounted difference in positive-state exposure is **1.30178 annual state-years** over five subsequent years (3% annual real discount, mid-year payment convention).\n')
md.append('Formula for a payer-specific credit: **Adjusted annual state-spending difference × 1.30178 × (1 − 0.53) × CMS recognition share**. This is a model-based standardized price, not a treatment-effect estimate. The 53% spontaneous-remission rate is from Whiteford et al. (2013), a systematic review of untreated major depression among primary care adults. It is fixed for these conditional estimates rather than estimated from MEPS.\n')
md.append('## Empirical and numerical validation\n')
md.append('- All four primary two-part regressions converged. The complete-data, full-design PSU variance uses 395 PSUs in 105 strata (290 design degrees of freedom); all four primary models are full rank. Two invalid-region person-year records (both without positive depressive screen) were excluded; the earlier claimed separation diagnostic is not archived.\n')
md.append('- Three coefficient coordinates per model component were checked against numerical finite differences; this was not a full-vector derivative or independent survey-variance validation. Matrix-based Markov propagation replicated the closed-form five-year factor, and 25 randomized transition matrices passed a second independent implementation.\n')
md.append('- The 75% and 50% case rates and interval endpoints were checked against exact scaling of the 100% estimates. No negative payment amounts and no payer sums are constructed; insurance-covered domains overlap.\n')
md.append('- A different mean estimator, Poisson pseudo-maximum likelihood with a log link (PPML), was fitted on the same covariates as an appendix-only check, never used to select the headline. Annual estimates are:\n')
md.append('| Payer | Primary two-part | Same-sample PPML check |')
md.append('|---|---:|---:|')
for payer in N:
 v=val.loc[payer]
 md.append(f'| {payer} | {dollars(v.two_part_primary)} | {dollars(v.single_part_PPML_validation)} |')
md.append('\n- Standard two-year MEPS panel records provided 2,430 positive-screen longitudinal pairs (weighted positive-to-positive transition rate **46.35%**), using samples that overlap with the four-wave analysis, consistent in magnitude with the four-year panel **48.84%** persistence estimate. The four-year data supply the additional *formerly-positive/remitted* recurrence transitions that two-year panels cannot measure.\n')
md.append('## Scope limitations material to CMS\n')
md.append('1. **Clinical construct:** PHQ-2 changing from ≥3 to below 3 at an approximately annual observation is only a proxy; it is *not* the exact CMS Quality ID #370 outcome, which requires diagnosed depression plus PHQ-9 >9 at index and PHQ-9 <5 at 12 months ±60 days. The MEPS annual data lack the required PHQ-9 and precise measurement timestamps.\n')
md.append('2. **Postremission association, not direct causal effect:** Annual MEPS health-state spending includes currently PHQ-2-negative individuals who may never have had depression. The primary model standardizes their predicted cost to baseline screen-positive covariates but cannot directly measure the costs of the actual *remitted* subgroup five years later. Prospective four-year remission-specific comparison remains imprecise, including a negative Medicare annual adjusted association; this discrepancy cannot be resolved by choosing the larger, positive estimate.\n')
md.append('3. **Projected horizon:** The five-year period is extrapolated beyond available individual follow-up, under a stationary two-state Markov model. Transition dates within years, death, structural persistence, and changes in real cost are not separately modeled. Mid-year discounted annual beginning-of-year state rewards may overstate savings if symptoms recur early within a year.\n')
md.append('4. **Financial meaning:** Medicare-paid expenditures among MEPS civilians are not the same as Medicare fee-for-service payment-standardized Part A/B/D claims, nor Medicare program savings net of intervention costs. Intervention expenses prior to documented remission are outside this valuation by design; unknown maintenance interventions during the future years cannot be identified separately.\n')
md.append('5. **Conditional uncertainty:** The 95% ranges include sampling variation and modeled remission/recurrent screen transitions, but exclude uncertainty in the 53% spontaneous-remission assumption, PHQ-2 proxy validity, confounding, choice of extrapolation model and dependence between annual and four-year sample estimates. Near-50% breakeven at 100% recognition is a mathematical consequence, not evidence of actual financial breakeven.\n')
md.append('## Actuarial status\n')
md.append('**The table is a complete provisional MEPS-based NPVoC rate card under the agreed formula. It is not sufficient evidence to assert the published amounts are realized or causally attributable Medicare savings, nor exact Quality ID #370 clinical-remission values.** The principal unresolved limitation is identifying *post-remission* savings rather than extrapolating a cross-sectional symptom-state spending contrast. The independent PPML check improves confidence in the annual expenditure association but does not resolve that underlying estimand gap.\n')
md.append('## References\n')
md.append('- Maryland Diabetes Incidence Outcomes-Based Credit (approved May 2, 2019): https://hscrc.maryland.gov/Documents/Modernization/OBC/Maryland%20Diabetes%20Incidence%20Outcome-Based%20Credit%20Methodology%20-%20approved.pdf\n')
md.append('- CMS 2026 MIPS Quality ID #370 (PHQ-9 definition): https://qpp.cms.gov/docs/QPP_quality_measure_specifications/CQM-Measures/2026_Measure_370_MIPSCQM.pdf\n')
md.append('- Whiteford et al. 2013, untreated depression remission meta-analysis: https://pubmed.ncbi.nlm.nih.gov/22883473/\n')
md.append('- BLS annual CPI-U values, national: https://www.bls.gov/regions/mid-atlantic/data/consumerpriceindexannualandsemiannual_table.htm\n')
(R/'FINAL_REPORT.md').write_text('\n'.join(md))
print('Wrote',R/'FINAL_REPORT.md')
