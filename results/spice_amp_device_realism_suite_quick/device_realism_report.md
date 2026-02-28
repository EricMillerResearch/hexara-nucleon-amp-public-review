# Device-Level Realism SPICE Suite

## Implemented Realism
- MOSFET output stage uses VDMOS `.model` with nonlinear capacitance params (`Cgdmax/Cgdmin/Cgs/Cjo`).
- Explicit PWM comparator + dead-time window logic (`DT_MARGIN`).
- Gate-driver source/sink current limits and UVLO/overcurrent inhibit (`IGSRC/IGSNK/UVLO/ILIM`).
- Nonlinear inductor saturation surrogate + battery chemistry droop RC network.

## tuned_parameters
- DT_MARGIN: 0.08
- FSW: 18000.0
- IGSNK: 0.42
- IGSRC: 0.35
- ILIM: 140.0
- MOD_GAIN: 2.2

## nominal_device_realism
- eff_pct: 0.699474
- i_max: 3.74437
- i_neg: -3.744366
- i_pos: 3.607898
- p_in: 439.178
- p_out: 3.071937
- vbat_min: 13.74448
- vbat_nom: 14.18053

## sag_14p4_to_11p5_full_output
- p_pre: 2.905236
- p_sag: 1.853363
- vbat_min: 10.90809

## output_short_5ms_device
- i_max: 60.0422
- i_neg: -39.75501
- i_pos: 60.04215
- p_pre: 2.870132
- p_recover: 2.868807

## Artifacts
- `results/spice_amp_device_realism_suite/device_realism_metrics.csv`
- `results/spice_amp_device_realism_suite/device_realism_summary.json`
- `results/spice_amp_device_realism_suite/tuning_candidates.csv`
- `results/spice_amp_device_realism_suite/tuning_selected.json`
- `results/spice_amp_device_realism_suite/device_realism_report.md`
