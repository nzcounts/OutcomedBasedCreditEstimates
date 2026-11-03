# Input archives

Required: MEPS.zip, More MEPS.zip, h36u24dta.zip. SHA-256 values are in
SOURCE_DATA_SHA256.txt. These are checksums of the original assembled ZIPs;
repacking identical component data changes ZIP hashes.

MEPS.zip contains MEPS/h216dta.zip, h224dta.zip, h233dta.zip, h243dta.zip,
h251dta.zip and h256dta.zip (each under MEPS/), for 2019-2024 annual files.
More MEPS.zip contains More MEPS/h236dta.zip and More MEPS/h245dta (1).zip
for the special four-wave panels. h36u24dta.zip supplies pooled design IDs.
The loader expects one Stata file in each nested archive. Preserve exact names.

Obtain the original assembled archives from the study team. Public MEPS component
files come from AHRQ, but this repository does not contain an independently
verified recipe for rebuilding the identical assembled ZIPs. The unused condition
loader has additional inputs; those are not required by the primary runner.

Set MEPS_DATA_DIR to the archive folder, or place them in ignored data/raw/.
Do not commit the archives or intermediate respondent records.
