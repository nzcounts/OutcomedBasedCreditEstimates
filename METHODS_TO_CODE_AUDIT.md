# Verification of the Depression Remission Manuscript Against Executed MEPS Code

**Audit date:** October 28, 2026  
**Scope:** main article (`Depression_Remission_Main_Article_Matching_Supplement.docx`), cited technical supplement (`Depression_Remission_Technical_Supplement_Cited.docx`), primary reproducibility ZIP, source MEPS ZIP files, and the earlier prospective-remission MEPS analysis archive. This is a computational and manuscript-to-code audit, **not an independent external audit of statistical validity**.

## Executive determination

**The primary numerical analysis is genuine and reproducible, but not every impression conveyed by the main Methods and supplement is justified.** The underlying cross-sectional cost regressions and projected rates were actually computed. There is no evidence that the logistic/Gamma models, survey PSU calculations, transition equations, alternative PPML fit, or simulations were invented. However, the final output is a *model-based pricing scenario based on contemporary PHQ-2 screen-state expenditure associations*, **not** a study that measures expenditure savings after observed PHQ-9 clinical remission. It is also important that the earlier remitter-specific prospective analysis, independently reproduced in this audit, estimates a discordant, imprecise Medicare expenditure difference.

**Required action before policy circulation:** use the accompanying `AUDITED_CORRECTED_Main_Article.docx` and `AUDITED_CORRECTED_Technical_Supplement.docx`, which explicitly distinguish actual estimation from assumptions, disclose the earlier prospective results, and correct the descriptions of sample-independent validation and remission-state timing. These revisions do **not** change the original computed rate card; they change its interpretation and reporting.

## Independently checked numerical reproducibility

- Verified the SHA-256 hashes of the actual input files `MEPS.zip`, `More MEPS.zip`, and `h36u24dta.zip` against `results/AUDIT.json` and `SOURCE_DATA_SHA256.txt`. All match.
- Verified the four primary Python scripts in `reproducibility/code/` are **byte-identical** to the earlier executed primary scripts.
- Copied those scripts into a fresh analysis directory; reran `run_final.py`, `validate_final.py`, and `generate_report.py` using the three actual MEPS inputs. All **10 aggregate result CSV/JSON files matched byte-for-byte** with the earlier archived results.
- Independently re-executed the earlier prospective analysis (`run_analysis.py`, `run_validation.py`, `test_math.py`). Every archived numerical results CSV and `validation.json` reproduced byte-for-byte. Its `AUDIT.json` differed only in the recorded execution duration (`elapsed_sec`), as expected.
- Annual analysis: **77,487 person-years**, **6,604** screen-positive; Medicare annual PHQ-2-state expenditure difference **+$8,498.91** (survey SE **$971.84**). Four-wave participants **4,496**; estimated state probabilities **0.2373854** (negative after any earlier positive -> positive) and **0.4884412** (positive -> positive). Projected five-year factor **1.3017825757**; spontaneous discount **53%**; reported Medicare 100% recognition rate **$5,199.95** (rounds to **$5,200**).
- The original prior prospective remitter-specific study included **690** screen-positive person-transitions from **526** distinct people and estimated a Medicare difference in later annual spending of **-$7,140.88** (95% CI **-$17,541.72 to +$3,259.96**). It was **not** the source of the primary +$5,200 rate card.

## Code-to-manuscript claim audit

| Assertion in the article/supplement | Determination | Grounding and necessary precision |
|---|---|---|
| Annual pooled 2019-2024 MEPS expenditure records were analyzed | **Implemented** | `run_final.py`, lines 36-93; six annual Stata archives are opened and pooled. |
| Two 2018-2021/2019-2022 special four-wave MEPS panel files were analyzed | **Implemented** | `enhanced_loader.py`, lines 9-12 and 68-84; `run_final.py`, lines 189-225. |
| Adults aged 18-85, PHQ-2 0-6, positive SAQ weights, valid spending and demographics were selected | **Implemented** | Annual selection `run_final.py:67-82`; four-wave selection `:196-203`. Education with negative codes was retained as an **unknown category**, so not every demographic missing value was excluded. |
| Two annual records with invalid region were excluded | **Verified** | Independently located one each in 2019 and 2021, both PHQ-2-negative; `REGION=-1`. The current package does **not** preserve the earlier alleged model separation diagnostic that motivated the exclusion; describe only the verified exclusion. |
| Weighted two-part logistic and positive-Gamma/log annual expenditure models were fitted | **Implemented** | `run_final.py:115-187`, `:130-133` and `:150-159`. Four models converged. |
| Annual spending models controlled for age, age squared, sex, race, poverty, education, insurance, region, year, and PHQ-2 screen status | **Implemented** | `run_final.py:123-125`. Physical comorbidity and depression diagnoses were **not adjusted for**. |
| State-specific predicted means were standardized to current screen-positive adults in each payer population | **Implemented** | `run_final.py:115-118` and `:143-163`. The screen-negative observations used for model fitting included persons without documented past depression. |
| Total, Medicare-paid, Medicaid-paid, and privately-insured payment amounts were modeled separately | **Implemented** | `run_final.py:38-41`, `:115-116`. The domains may overlap and are not sum-able. |
| Costs converted to 2024 CPI-U dollars | **Implemented** | `run_final.py:36`, `:69-73`; 2024 target year set at `:146-149`. |
| Survey strata, PSUs, and weights were incorporated | **Implemented with precise specification** | Weighted GLMs and a **custom** linearized ultimate-cluster influence-function covariance (`run_final.py:95-113`, `:136-164`, `:217-219`). This was not a black-box survey GLM with built-in design SEs. AHRQ confirms that annual 2019-2024 PUF variance identifiers are compatible and four-wave SAQ analysis should use `LSAQWT`. |
| Annual model estimates measured individual postremission spending savings | **NOT DONE** | Annual outcome and PHQ-2 state are measured for the **same** person-year (`run_final.py:47-93`, `:115-125`). No longitudinal identified-remitter expenditure outcome entered the primary rate card. This is the principal estimand mismatch. |
| The model observed the exact CMS 12-month PHQ-9 clinical remission endpoint | **NOT DONE** | No PHQ-9, eligible clinical diagnosis criterion, +/-60-day timing, or CMS #370 patient-level eligibility was implemented. PHQ-2 states are research proxies. |
| The five postremission years were observed in a cohort | **NOT DONE; projected** | `run_final.py:248-263` initializes two projected hypothetical states and applies 5 annual rewards. Neither individual five-year observation nor postassessment Medicare claims are present. |
| Longitudinal relapse probability after a *newly documented 12-month remission* was estimated | **PARTLY MISDESCRIBED** | The 23.7% rate uses **all currently screen-negative states with any previously observed positive screen** (`run_final.py:207-216`). Of 444 R-state transitions, **101 (22.7% unweighted)** had already been screen-negative in the preceding wave. They were not newly resolved positive-to-negative screens. |
| Four-year panel spending was used to estimate postremission expenditure | **NOT DONE IN FINAL MODEL** | Four-wave spending variables enter as nonnegative **eligibility checks** (`run_final.py:198-201`) but not as a financial outcome for the annual cost contrasts; only PHQ-2 transitions are fitted from this panel. The earlier prospective analysis **did** use subsequent-year spending, but its estimate was excluded from the published primary rate. |
| A fixed 53% spontaneous-remission adjustment was applied | **Implemented as assumption** | `run_final.py:42`, `:297-305`. Whiteford et al. (2013) reported 53% untreated 12-month remission for adult primary care major depression; this does **not** estimate the attributable share of MEPS screen-state transitions. |
| A stationary 2-state model, 3% real midyear discount, and 100/75/50% rates were computed | **Implemented** | `run_final.py:248-263`, `:288-321`; matrix and arithmetic checks passed. This is a policy scenario, not a fitted treatment-effect model. |
| Simulated 120,000 draws with annual cross-payer and within-transition covariance | **Implemented, conditional** | `run_final.py:275-286`. Annual vs longitudinal covariance was set to zero **despite actual respondent overlap**; structural uncertainty and the 53% input were excluded. |
| A standalone PPML alternative estimate was computed | **Implemented** | `validate_final.py:13-39`, using the **same annual MEPS observations**, not an independent cohort. Results have the same direction, but cannot validate causal postremission effects. |
| Independent two-year panel validation was done | **OVERSTATED** | `run_final.py:227-246` merges the pooled annual data, so samples overlap. Independent audit found **870/2,430** positive pairs belong to the four-wave analytic population and **1,206/2,430** to the four-wave source before analytic exclusions. It is a useful descriptive consistency check, **not independent external validation**. |
| Full derivative checks and independent survey variance package validation were done | **OVERSTATED IF IMPLIED** | Finite difference gradients were verified at three coefficient coordinates per component (`run_final.py:166-174`), not the full vector; no independent survey-variance implementation or bootstrap validation was run. The alternative PPML checks the expenditure mean, not variance validity. |
| A separate prospective remission-specific analysis found negative Medicare contrast | **TRUE; material and underemphasized** | Earlier archive `MEPS_depression_remission_analysis_2026-10-28.zip` contains source code and numerical outputs. Independently rerun with the original MEPS files; annual Medicare estimate **-$7,141**, 95% CI crossing zero. It should be disclosed plainly in the main article, not only briefly in the supplement. |
| Program-specific Medicare savings, intervention ROI, or financial break-even were estimated | **NOT DONE** | Credit exceedance probabilities are based on the **same model's simulated valuations vs its own derived posted price** (`run_final.py:295-322`). They are **not** probabilities of net program savings. |
| Source code and outputs support reproducibility | **Verified** | All published script hashes match; all 10 final aggregate files reproduced byte-for-byte. External replication, clinical audit, and causal validity remain unverified. |

## Methodological considerations that were not performed

The analysis **did not** implement a diagnosed-depression cohort; PHQ-9 remission confirmation; intervention assignment or matched control groups; propensity-score balancing; individual fixed-effects causal estimation in the final rate card; longitudinal claims-based postremission cost attribution; payer-specific spontaneous-remission estimates; sensitivity analyses varying the 53% rate or Markov structure; parameter uncertainty for PHQ-2/PHQ-9 construct mapping; mortality, insurance-switching, or maintenance-treatment-cost trajectories; independent out-of-sample cost prediction; or a comparison with external Medicare claims. A prior separate research track contained some alternative prospective and fixed-effects analyses but **they were not included in the primary 2026-10-28 valuation model**. Citation to a methodological source is not evidence that its specific algorithm or reporting checklist was applied.

These omissions are not necessarily coding bugs or promises made explicitly by the Methods, but they are substantive limits on what the reported numbers can establish. In particular, **a reproducible point estimate can still target the wrong policy outcome**.

## Independent data-source documentation checks

The following documentation was compared with the implemented design:

1. AHRQ HC-256 annual documentation confirms that `SAQWT24F` is the appropriate 2024 adult self-administered questionnaire weight: https://meps.ahrq.gov/data_stats/download_data/pufs/h256/h256doc.shtml
2. AHRQ HC-236 confirms four-wave `LSAQWT` is appropriate for SAQ respondents with `SAQRDS2468=1`: https://meps.ahrq.gov/data_stats/download_data/pufs/h236/h236doc.shtml
3. AHRQ HC-036 explains that 2019-2024 annual PUFs may pool their original common variance identifiers, and `STRA9624`/`PSU9624` is used for linked panels: https://meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h036/h36u24doc.shtml
4. Whiteford et al. (2013) confirms the literature 53% estimate, based on 19 included studies, relates to **untreated major depression**, not to a directly identified intervention effect: https://pubmed.ncbi.nlm.nih.gov/22883473/

## Corrections enacted in companion audited documents

The corrected main article and supplement explicitly state that (1) the primary cost model is cross-sectional and uses screen-negative persons with no required past positive screen, (2) the 12-month landmark and five later years are imposed in a projection, (3) state R includes previously negative after past positive screens and is not restricted to newly remitted people, (4) the two-year check and PPML are not independent-data validation, (5) the simulations omit cross-source covariance despite overlapping MEPS respondents, (6) historical separation diagnostics are not archived and gradient checking was limited, and (7) the earlier prospective Medicare result was negative and imprecise. No headline credit or numerical confidence bound was recalculated or silently changed.

**Suggested actuarial framing:** “A reproducible, policy-scenario valuation of a PHQ-2 symptom-state expenditure association, projected over five hypothetical postlandmark years and reduced by a fixed literature-based natural-remission pricing factor.” Do **not** call the computed $5,200 a validated remission-related Medicare savings credit. Before advancing an actual remission outcome-based credit, prioritize a pre-specified analysis of **postassessment expenditures among actual clinically remitted vs otherwise similar persistently symptomatic patients** with clinical PHQ-9 and payer claims, ideally with causal identification or well-defined sensitivity bounds.

## Provenance and checksums

- `independent_rerun/`: unchanged original primary code, rerun outputs and logs.
- `prior_prospective/`: earlier separately executed remitter-specific analysis code and numerical output, rerun using original source archives.
- `independent_run.log`, `independent_validation.log`, `prospective_rerun.log`, `prospective_validation.log`, `overlap_transition_check.log`: audit-run logs.
- `rerun_checksums.txt`, `prospective_archive_hashes.txt`: checksum inventories.
- `revise_text_for_verified_methods.py`: transparent manuscript modification code; every change is auditably specified.

The original respondent-level MEPS ZIP archives are **not** redistributed with this audit. The audit did not involve an independent human statistician or any representation that CMS has reviewed/approved these estimates.
