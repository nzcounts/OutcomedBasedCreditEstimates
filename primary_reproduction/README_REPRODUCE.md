# Reproducing the published-style MEPS remission valuation

This archive contains code, aggregate outputs, and validation logs. It **does not contain MEPS microdata**. Obtain the three archives (MEPS.zip, More MEPS.zip, h36u24dta.zip) from the authorized original sources and ensure exact SHA-256 values in SOURCE_DATA_SHA256.txt before running. MEPS.zip and More MEPS.zip are assembled from AHRQ publicly released files. Original file names required by the code must be retained.

Run from this directory:

```sh
export MEPS_DATA_DIR=/path/to/your/source_zips
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python code/run_final.py
python code/validate_final.py
python code/generate_report.py
```

Software environment recorded in requirements_recorded.txt. The original run was based on the provided files, not rerun as part of adding citations. See results/AUDIT.json, results/VALIDATION.json, execution.log, rerun.log and validation.log.

Interpretation: these results are model-based PHQ-2 screen-state valuations, not an empirical PHQ-9-confirmed remission value or causal net Medicare savings. The 'breakeven' probability is conditional value exceeding the posted credit, NOT ACO program breakeven.
