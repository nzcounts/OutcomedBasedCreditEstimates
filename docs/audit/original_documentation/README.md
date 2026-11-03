# Reproducible MEPS depression remission valuation

The two inputs are supplied previously by the user: MEPS.zip and More MEPS.zip, plus h36u24dta.zip. This release contains NO respondent-level MEPS records.

To reproduce, place original user ZIP files in the same directory or point `MEPS_DATA_DIR` to that directory and execute:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python code/run_final.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python code/validate_final.py
python code/generate_report.py
```

Python requirements: numpy, pandas, scipy, statsmodels, patsy.

Primary table: `results/FINAL_100_75_50_AND_BREAKEVEN.csv`.
Technical methods/results: `FINAL_REPORT.md`.
The code automatically checks source file SHA256, marginal derivative mathematics, survey model convergence, Markov propagation, and exact recognition scaling.

NOT PHQ-9-confirmed clinical remission, NOT causal program savings, and NOT an ACO financial breakeven calculation.
