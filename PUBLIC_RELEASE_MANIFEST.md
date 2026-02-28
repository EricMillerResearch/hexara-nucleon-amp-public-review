# Public Release Manifest

Date: 2026-02-28

## Purpose

Sanitized open-source peer-review package with reproducible simulation evidence.

## Included Paths

- `README.md`
- `REPRODUCIBILITY.md`
- `PEER_REVIEW_CHECKLIST.md`
- `LIMITATIONS.md`
- `RESULTS_SUMMARY.md`
- `CITATION.cff`
- `requirements.txt`
- `requirements.lock`
- `RUN_METADATA.json`
- `SHA256SUMS`
- `verify_release.sh`
- `LICENSE`
- `scripts/run_spice_amp_validation_suite.py`
- `results/spice_amp_10kw_dsp_suite/*.csv`
- `results/spice_amp_10kw_dsp_suite/suite_summary.json`
- `results/spice_amp_10kw_dsp_suite/suite_report.md`
- `results/spice_amp_device_realism_suite_quick/device_realism_report.md`

## Explicitly Excluded

- `hardware/`
- `results/amp_manufacturing_package/`
- raw SPICE netlists from generated outputs (`*.cir`)
- raw simulator logs (`*.log`)
- detailed BOM and sourcing internals
- unpublished commercial implementation details
