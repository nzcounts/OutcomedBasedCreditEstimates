# Results guide

The files in primary/ are unchanged recorded outputs from the original repository.
All monetary estimates use constant 2024 US dollars. Payer populations overlap;
do not sum their estimates. Missing values do not mean zero.

| File | Interpretation |
|---|---|
| FINAL_100_75_50_AND_BREAKEVEN.csv | Four payer targets at 100/75/50% recognition; signed valuations, nonnegative candidate payments and conditional intervals. |
| annual_primary_models.csv | Cross-sectional positive-minus-negative PHQ-2 spending contrasts and survey uncertainty. |
| annual_sample_by_year.csv | Annual eligibility counts and spending summaries; source totals precede inflation conversion. |
| four_year_transition_covariance.csv | Covariance of negative-after-prior-positive to positive and positive to positive transition estimates. |
| joint_payer_survey_covariance.csv | Cross-payer covariance of annual expenditure contrasts. |
| projected_five_year_contributions.csv | Discounted projected state-years and annual contributions; not five observed years after remission. |
| two_year_panel_transition_check.csv | Descriptive transitions from overlapping two-year samples. |
| APPENDIX_independent_PPML.csv | Alternative expenditure mean model using the same annual observations; not independent-data validation. |
| AUDIT.json | Recorded sample, transition, design and input-hash metadata. |
| VALIDATION.json | Recorded arithmetic checks and alternative-model results. |

`conditional_probability_valuation_exceeds_payment` compares simulated valuations
with the proposed price. It is not a probability of net program savings or ACO
financial break-even. The 53% factor and projection structure are fixed assumptions.
Intervals omit cross-source covariance and structural/causal uncertainty.
`annual_remitted_state_cost_2024usd` is a legacy field name for a standardized
negative-screen mean; a clinically remitted cohort was not identified.

Original field names and numerical cells are preserved to maintain compatibility.
See the [earlier prospective results](../prior_prospective_reproduction/TECHNICAL_RESULTS.md)
for the different longitudinal comparison. Original report prose is archived under
docs/audit/original_documentation; use the current audited manuscripts for interpretation.
