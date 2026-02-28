# Results Summary (From Current Artifacts)

Source files:
- `results/spice_amp_10kw_dsp_suite/suite_report.md`
- `results/spice_amp_10kw_dsp_suite/suite_summary.json`
- `results/spice_amp_device_realism_suite_quick/device_realism_report.md`

## Core DSP Suite Highlights

- Step load change: `p_out_pre=10717.89`, `p_out_post=19649.38`, `i_max=199.8264`
- Rail sag: `p_out_pre=10953.98`, `p_out_post=8102.053`, `u_max=0.9798169`
- 0.25 ohm stress: `i_max=512.081`, `u_max=0.98`, `u_min=-0.98`
- Hard clipping recovery: `p_out_clip=13350.02`, `p_out_recover=4813.23`
- Thermal foldback test file reports: `temp_max=0.08204867`, `temp_end=0.0817618`

## THD Trend

From `thd_vs_power` in `suite_summary.json`:
- 0.2 vref: THD `0.061%`
- 0.8 vref: THD `0.247%`
- 0.9 vref: THD `3.539%`
- 1.0 vref: THD `7.862%`

Interpretation: distortion remains low through mid-drive region and rises sharply near saturation.

## Device Realism Suite Snapshot

From `device_realism_report.md`:
- Includes nonlinear MOSFET model behavior, dead-time logic, gate driver current limits, UVLO/overcurrent inhibit, and droop/saturation surrogates.
- Tuned parameter examples: `DT_MARGIN=0.08`, `FSW=18000`, `ILIM=140`, `MOD_GAIN=2.2`.

## Reviewer Note

These values are simulation outputs under modeled assumptions. Use with `LIMITATIONS.md` and `HANDOFF.md` when assessing claims.
