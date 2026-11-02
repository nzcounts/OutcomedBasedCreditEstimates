# Remission case-rate analysis — 2026-10-28

The reproducible empirical package and results are documented in `TECHNICAL_RESULTS.md`.

Inputs from user, NOT redistributed:
- `MEPS.zip`
- `More MEPS.zip`
- `h36u24dta.zip`

Run in shell:
```
python -m pip install numpy pandas scipy statsmodels patsy
export MEPS_DATA_DIR=/path/to/three/user-supplied/archives
export OPENBLAS_NUM_THREADS=1
python run_analysis.py
python run_validation.py
python test_math.py
```

`results/credits_100_75_50.csv` is the primary output; `results/AUDIT.json` includes source hashes. Source data remain outside the delivery ZIP. None of the output tables are person-level files. This is a provisional PHQ-2-screen proxy valuation, not a certified clinical remission Medicare savings credit.
