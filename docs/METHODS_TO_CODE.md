# Methods to code

| File/function | Purpose |
|---|---|
| src/enhanced_loader.py | Read nested Stata archives and four-wave panels. |
| src/run_final.py: annual_data | Assemble annual samples, weights, prices and covariates. |
| design_variance, unit_sum | Aggregate influence scores by PSU and stratum. |
| primary_model | Two-part annual expenditure models and standardized contrasts. |
| longitudinal_4wave, two_year_audit | Four-wave transitions and overlapping-sample descriptive check. |
| projection | Discount hypothetical annual state differences over five years. |
| headline, run | Combine estimates, simulate conditional uncertainty and export tables. |
| src/validate_final.py | Stored-output arithmetic and same-sample PPML alternative. |
| src/generate_report.py | Format the numerical results with interpretation limits. |
| tools/check_overlap_and_transition.py | Reproduce source/analytic sample-overlap counts. |

Functions and their calculation order are retained rather than introducing an
additional package layer. Parameters remain explicit in run_final.py: CPI factors,
SPONT=0.53, R=0.03, DRAWS=120000 and SEED=20261028. Changing these is a substantive
analysis revision, separate from this repository reorganization.

The historical audit gives the detailed estimand limitations and source line
references as they stood at the original commit. Those references are historical,
not current line numbers. No causal identification or variance-validation claim
has been added by reorganizing the files.
