# Hexara Nucleon Amp: Public Peer-Review Release

This folder contains the sanitized public package for academic/technical peer review.

## Included

- Reproducibility and review docs
- Core SPICE validation script
- Sanitized result artifacts
- Locked dependency file (`requirements.lock`)
- Integrity/provenance files (`SHA256SUMS`, `RUN_METADATA.json`)

## Excluded by Design

- Detailed hardware implementation files
- BOM sourcing/commercial strategy
- Internal manufacturing/compliance playbooks

## Run

```bash
python3 -m pip install -r requirements.lock
python3 scripts/run_spice_amp_validation_suite.py
```

## Verify

```bash
shasum -a 256 -c SHA256SUMS
```

## Reviewer Docs

- `REPRODUCIBILITY.md`
- `PEER_REVIEW_CHECKLIST.md`
- `LIMITATIONS.md`
- `RESULTS_SUMMARY.md`
