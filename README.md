# Outcomes-based credit estimates

Reproducible MEPS-based valuation of PHQ-2 symptom-state expenditure associations
under a five-year policy-pricing scenario. Annual expenditure models and observed
screen transitions feed a projection with 3% real discounting and a fixed 53%
natural-remission adjustment. These estimates do not identify clinical-remission
or intervention-caused savings.

## Start here

- [Current article and supplement](manuscript/README.md)
- [Primary results and interpretation](results/README.md)
- [Reproduce the analysis](docs/REPRODUCIBILITY.md)
- [Methods and code map](docs/METHODS_TO_CODE.md)
- [Historical methods audit](docs/audit/METHODS_TO_CODE_AUDIT.md)
- [Earlier prospective analysis](prior_prospective_reproduction/README.md)

The earlier prospective analysis targets a different comparison and is retained
for transparency; it did not generate the primary pricing table. Its discordant,
imprecise Medicare estimate remains a material interpretive limitation.

## Layout

`src/` contains the four primary Python modules; `results/primary/` contains the
recorded aggregate outputs. `manuscript/` holds the current audited manuscripts;
`docs/audit/` holds historical evidence and `tools/` holds supporting utilities.
The recorded package versions are in `requirements.txt`.

For a new execution, set `MEPS_DATA_DIR` and `MEPS_OUTPUT_DIR`, then run
`python src/run_final.py`, `python src/validate_final.py`, and
`python src/generate_report.py` in that order. Follow the reproduction guide for
environment setup, archive checks and validation. No microdata are included.

No project licence or author attribution has been invented by this reorganization.
