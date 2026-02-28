# Reproducibility Protocol

## Environment

Required tools:
- `python3` (3.9+ recommended)
- `ngspice`

Dependency options:
- Flexible: `python3 -m pip install -r requirements.txt`
- Locked: `python3 -m pip install -r requirements.lock`

## Run

From repository root:
```bash
python3 scripts/run_spice_amp_validation_suite.py
```

## Expected Outputs

- `results/spice_amp_10kw_dsp_suite/suite_metrics.csv`
- `results/spice_amp_10kw_dsp_suite/thd_vs_power.csv`
- `results/spice_amp_10kw_dsp_suite/suite_summary.json`
- `results/spice_amp_10kw_dsp_suite/suite_report.md`

## Integrity Verification

Verify artifact and file integrity:
```bash
shasum -a 256 -c SHA256SUMS
```

Run provenance and tool versions:
- `RUN_METADATA.json`

## Caveats

- Minor numeric differences can occur across tool versions.
- Results are model-level simulation outputs, not certified hardware test results.
