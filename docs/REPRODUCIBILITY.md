# Reproduction

Run commands from the repository root with Python 3.11 or later. The original
repository records package versions, but not a complete operating-system/Python
environment lock. `requirements.txt` preserves those recorded versions exactly.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export MEPS_DATA_DIR="/absolute/path/to/source_archives"
export MEPS_OUTPUT_DIR="$PWD/runs/reproduction"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python tools/verify_inputs.py
python -m unittest discover -s tests -v
python src/run_final.py
python src/validate_final.py
python src/generate_report.py
```

Three archives are required: `MEPS.zip`, `More MEPS.zip`, and `h36u24dta.zip`.
See [input guidance](../data/README.md). The explicit input check compares SHA-256
against the recorded specifications before fitting; the original analysis records
hashes at completion, which alone does not validate the inputs in advance.

Without MEPS_DATA_DIR, current primary code looks in `data/raw/` relative to the
repository, regardless of the working directory. Without MEPS_OUTPUT_DIR it writes
to `results/primary/`, overwriting recorded files. Use the fresh `runs/` path above
to preserve the shipped results. Relative environment paths resolve from the
process working directory; absolute paths are recommended.

`validate_final.py` includes a same-sample PPML refit and needs the input data.
The unittest suite is data-free: it checks the projection against matrix iteration,
stored table arithmetic and preservation of recorded results. Neither substitutes
for a new full-data fit. The current restructuring did not rerun the MEPS analysis.

The report generator writes FINAL_REPORT.md into MEPS_OUTPUT_DIR; it does not
modify the root README or manuscript documents. Report prose has been corrected
to match the historical audit. A rerun AUDIT.json will also have corrected
`definition` prose; that expected text difference is not a numerical change.

The earlier prospective scripts remain as archived. To run them, keep the same
MEPS_DATA_DIR setting, change into `prior_prospective_reproduction/`, and follow
its README. They write to their own results directory, so use a separate checkout
for that reproduction. Historical logs/checksums describe their original paths.
