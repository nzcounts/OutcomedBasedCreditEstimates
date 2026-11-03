# Historical audit evidence

Original logs, checksum files, citation checks and METHODS_TO_CODE_AUDIT.md are
preserved verbatim. Their historical timestamps, machine paths, directory names
and line numbers document the original execution, not the current checkout.
original_documentation/ preserves superseded README and report prose for traceability.
Use the root README and docs/REPRODUCIBILITY.md for current execution instructions.

REORGANIZATION_MANIFEST.json maps every originally tracked file to its destination
and records hashes. Source functions were checked for AST equivalence after
excluding docstrings; only the documented path/interface changes are permitted.
The report generator also changes interpretation prose and its write destinations.
Existing CSV/JSON results and manuscript files were not changed or recomputed.
This reorganization does not repeat the historical full-data reproduction claims.
