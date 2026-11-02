# MEPS depression remission: five-year fixed case-rate estimation

## Executive finding

**The analysis has been executed on the uploaded MEPS individual-level data. It does not establish a defensible positive Medicare credit.** The Medicare-associated remission estimate is negative and imprecise; the all-medical and private-insurer intervals include zero. The Medicaid point estimate is positive, but based on a small observational panel and the conditional interval is borderline. No output should be characterized as causally established savings.

### Primary output: 2024-dollar fixed per-remission rates

The values below are signed model outputs. **A negative number is not a proposed payable credit**; it means these data do not support an affirmative credit of that amount. Conditional model-parameter 95% intervals are not complete uncertainty about clinical measurement, confounding or extrapolation.

| Population | 5-year value before spontaneous discount | 100% credit (95% interval) | 75% credit (95% interval) | 50% credit (95% interval) |
|---|---:|---:|---:|---:|
| All medical expenditures | $3,579 | $1,682 (-$1,251 to $4,666) | $1,261 (-$938 to $3,500) | $841 (-$625 to $2,333) |
| Medicare paid | -$9,296 | -$4,369 (-$10,852 to $1,942) | -$3,277 (-$8,139 to $1,456) | -$2,185 (-$5,426 to $971) |
| Medicaid paid | $5,623 | $2,643 ($54 to $5,325) | $1,982 ($40 to $3,994) | $1,321 ($27 to $2,663) |
| Private insurer paid | $3,794 | $1,783 (-$1,276 to $4,806) | $1,337 (-$957 to $3,604) | $892 (-$638 to $2,403) |

### Observed and adjusted one-year post-assessment spending differences

Positive values mean predicted future expenditure is higher among those who remain screen-positive at the annual assessment. Negative values mean the reverse.

| Population | Person-transitions | Distinct people | Observed unadjusted difference | Two-part adjusted difference (95% survey CI) |
|---|---:|---:|---:|---:|
| All medical expenditures | 690 | 526 | $3,924 | $2,749 (-$2,082 to $7,580) |
| Medicare paid | 321 | 244 | $928 | -$7,141 (-$17,542 to $3,260) |
| Medicaid paid | 296 | 220 | $5,531 | $4,319 ($58 to $8,581) |
| Private insurer paid | 230 | 194 | $603 | $2,914 (-$2,113 to $7,941) |

## Exact target and data

- Two pooled four-year special MEPS panels, 2018–2021 and 2019–2022, linked to annual MEPS financial, demographic, coverage, and socioeconomic variables and HC-036 survey sampling units.
- Four-wave complete records: **4,496**; baseline-positive eligible remission transitions: **690**; distinct people in remission comparison: **526**.
- Index: PHQ-2 score 3–6 at annual wave *t*. Remission proxy: PHQ-2 score 0–2 at wave *t+1*. Comparison: PHQ-2 stays 3–6 at wave *t+1*.
- Expenditure outcome: reported payments in calendar year *t+2*, after the year of the remission assessment, adjusted to 2024 purchasing power with annual U.S. CPI-U.
- Payer populations represent people covered by the indicated payer during the remission-assessment year. These payer domains overlap; payer amounts must not be added.
- These are repeated person-transitions from 526 individuals, not 690 independent people.

## Statistical specification

1. **Maryland-style two-part expenditure model** for each payer domain. Probability of any spending: survey-weighted Binomial/logit GLM; spending conditional on positive: survey-weighted Gamma/log GLM; predicted spending is the product. Covariates: age and age squared, sex, race group, poverty category, education (years; missing flagged if any), insurance, geographic region, calendar year, and baseline PHQ-2 severity. No six-condition expanded adjustment. Sparse categories were consolidated and education was modeled linearly to ensure convergence in limited payer-domain samples.
2. **Standardized annual expenditure contrast:** Within baseline screen-positive patients, predict one subsequent year of cost under the counterfactual status “remitted” vs “persistent,” for the same covariate distributions and survey weights; subtract predicted cost for remitted from persistent.
3. **Natural-history projection:** Estimate screen-positive persistence and re-positivity after previous remission from four-wave trajectories. The weighted estimates are P(P next | P now) = 0.488 and P(P next | previously positive, now negative) = 0.237. Assume these transition probabilities persist over five future annual intervals. This is a projection assumption, not five observed follow-up years.
4. **Five-year real present value**, discount rate 3% per annum, mid-year. Let q=P(P next | P now)-P(P next | R now), and K=sum[q^k/(1.03)^(k+0.5)] for k=0,...,4. Estimated K=1.301783. Five-year value = annual adjusted spending difference times K.
5. **Pre-agreed policy pricing**: spontaneous-remission rate fixed at 53%; base rate = five-year value times (1 - 0.53); recognition rates = 100%, 75%, 50%. No intervention-specific effectiveness, no observed provider remission rate, no practice-level reconciliation or incidence multiplier.
6. **Uncertainty**: survey-stratified PSU-level Taylor linearization of two-part standardized prediction margins and 2-state transition probabilities, joined into a 6-by-6 covariance matrix preserving overlap. 200,000 fixed-seed normal parameter simulations produce 2.5th and 97.5th percentiles. The 53% policy factor is fixed, so intervals are conditional on it.

## Diagnostics and independent checks

- The sampling frame contained **294 PSUs in 117 strata**, with **177** design degrees of freedom and no singleton strata.
- All primary logistic and Gamma-log fits converged; model matrices were full rank and observed costs were nonnegative. Source payer payments did not exceed the corresponding total.
- Annual MEPS PHQ-2 and insurance status matched their four-year panel records for every linked remission-assessment observation.
- Transition rates and design covariance independently reproduce estimates from the previously executed four-year MEPS analyses (numerical difference below 1e-14).
- Independent survey-weighted linear regressions reproduce direct-remission cost comparisons at approximately the same scale and confirm the negative Medicare association; code checks their coefficients against statsmodels WLS.
- Numerical finite differences validate marginal-standardization derivatives for both model components; direct state-matrix propagation matches the closed-form five-year extrapolation.
- All 75% and 50% credit values, including interval endpoints, equal precisely 0.75 and 0.50 times the 100% estimates; joint covariance is positive semidefinite.

### Independent survey-linear sensitivity results

| Population | Linear adjusted difference (95% CI) | Linear adjusted + baseline prior spending (95% CI) |
|---|---:|---:|
| All medical expenditures | $2,421 (-$2,989 to $7,830) | $485 (-$4,612 to $5,581) |
| Medicare paid | -$4,188 (-$14,350 to $5,973) | -$6,790 (-$16,708 to $3,127) |
| Medicaid paid | $4,292 ($265 to $8,320) | $4,304 ($370 to $8,237) |
| Private insurer paid | $1,241 (-$2,783 to $5,264) | $358 (-$3,754 to $4,470) |

## Interpretation and decision relevance

**This study does not yield a reliable positive Medicare remission credit.** Its conditional main estimate is negative, and the interval includes both substantial cost increases and savings. The 100/75/50 percentages reduce magnitude but cannot fix a negative, uncertain underlying estimate. The all-payer and private positive point estimates are also not distinguishable from zero under the main sampling-uncertainty calculation.

The Medicaid association is positive in the main and linear diagnostics. However, only 296 person-transitions contributed to that payer domain, the margin is observational, and the CI does not incorporate the larger uncertainties described below. It should not be interpreted as a validated causal Medicaid savings rate.

### Essential limitations

- **Measurement**: PHQ-2 below 3 is resolution of a depressive symptom screen, not clinical PHQ-9 remission; not all screen-positive adults have a confirmed depression diagnosis.
- **Attribution**: The 53% figure is a published *untreated MDD* 12-month remission estimate in primary-care adults; it does not identify the fraction of MEPS screen-negative cases caused by interventions. The (1 - 0.53) multiplication is a standardized pricing convention.
- **Causality**: Even after adjustment, baseline disease course, severity, medical comorbidity, healthcare access, treatment changes and regression to the mean can affect both remission and future spending. No intervention control group is observed.
- **Time horizon**: Only four calendar years are observed; this projects five future post-assessment years from a stationary Markov assumption, without modeling mortality or healthcare-sector cost growth separately.
- **Population/time**: Results describe 2018–22 special-panel completers and exclude institutionalized populations. National Medicare-paid MEPS data are not the same as Medicare fee-for-service Parts A/B/D program outlays.
- **Uncertainty**: The 95% intervals incorporate measured sampling and cost/transition model parameters, but exclude clinical-outcome misclassification, causal confounding, projection structure, uncertain spontaneous-remission benchmark and policy implementation risk.

## References

Maryland Diabetes Outcomes-Based Credit Methodology (2019): https://hscrc.maryland.gov/Documents/Modernization/OBC/Maryland%20Diabetes%20Incidence%20Outcome-Based%20Credit%20Methodology%20-%20approved.pdf

Whiteford et al. (2013), *Estimating remission from untreated major depression: A systematic review and meta-analysis* (12-month 53% estimate): https://pubmed.ncbi.nlm.nih.gov/22883473/

IPUMS MEPS, PHQ-2 questionnaire interpretation: https://meps.ipums.org/meps-action/variables/PHQ2

U.S. Bureau of Labor Statistics, annual CPI-U: https://www.bls.gov/regions/mid-atlantic/data/consumerpriceindexannualandsemiannual_table.htm

### Reproduction

The archive includes `run_analysis.py`, `run_validation.py`, `test_math.py`, the public-use archive loader, this report, the full CSV outputs, a source-hash audit and execution logs. It excludes respondent-level MEPS data. To rerun, provide the four user-supplied ZIP inputs at `MEPS_DATA_DIR` (`MEPS.zip`, `More MEPS.zip`, `h36u24dta.zip`; the BRR ZIP was provided but is not used by this analysis). Run the two scripts with `OPENBLAS_NUM_THREADS=1` on Python with numpy/pandas/statsmodels/patsy/scipy.

**No code review can prove an arbitrary program bug-free.** The listed checks provide evidence that the executed implementation matches the stated estimand and passed the performed numerical validations.
