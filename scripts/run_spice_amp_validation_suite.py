#!/usr/bin/env python3
"""Run DSP amp SPICE validation suite:
1) Step response to sudden load change
2) Rail sag simulation
3) 0.25 ohm stability test
4) Hard clipping recovery
5) Thermal foldback behavior
6) THD vs power curve
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Dict, List

import numpy as np


OUT = Path("results/spice_amp_10kw_dsp_suite")
BASE_FREQ = 1000.0

PARAMS = {
    "VRAIL_NOM": 100,
    "VBATT_NOM": 14.4,
    "ETA_DC": 0.92,
    "R_SAG": 0.03,
    "R_WIRE": 0.01,
    "NPAR": 6,
    "T_AMB": 25,
    "T_FOLD": 85,
    "T_SOFT": 6,
    "RTH": 0.02,
    "CTH": 1,
    "PTH_SCALE": 2500,
}


def run_ngspice(netlist: str, name: str) -> tuple[Path, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    cir = OUT / f"{name}.cir"
    log = OUT / f"{name}.log"
    cir.write_text(netlist, encoding="utf-8")
    cmd = ["ngspice", "-b", "-o", str(log), str(cir)]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"{name}: ngspice failed (code {cp.returncode})\n{cp.stdout}\n{cp.stderr}\n{log.read_text()}")
    return cir, log


def parse_meas(log_path: Path) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if "=" not in s:
            continue
        lhs, rhs = s.split("=", 1)
        key = lhs.strip().lower()
        if key in {"vout_rms", "iout_rms", "p_out", "u_min", "u_max", "i_pos", "i_neg", "i_max", "p_out_pre", "p_out_post", "p_out_clip", "p_out_recover", "temp_max", "temp_end"}:
            try:
                out[key] = float(rhs.split()[0])
            except Exception:
                pass
    return out


def parse_wrdata(path: Path, vec_names: List[str]) -> Dict[str, np.ndarray]:
    a = np.loadtxt(path)
    if a.ndim == 1:
        a = a.reshape(1, -1)
    out = {}
    # ngspice wrdata writes (x,y) pair for each vector -> use odd columns as values.
    for i, name in enumerate(vec_names):
        col = 2 * i + 1
        if col < a.shape[1]:
            out[name] = a[:, col]
    return out


def thd_from_wave(t: np.ndarray, x: np.ndarray, f0: float, nharm: int = 10) -> float:
    # Uniform-sampling assumption from fixed-step transient.
    dt = float(np.median(np.diff(t)))
    x = x - np.mean(x)
    n = len(x)
    w = np.hanning(n)
    xw = x * w
    X = np.fft.rfft(xw)
    freqs = np.fft.rfftfreq(n, dt)
    def amp_at(f):
        idx = int(np.argmin(np.abs(freqs - f)))
        return float(np.abs(X[idx]))
    a1 = amp_at(f0)
    if a1 <= 1e-12:
        return float("nan")
    hs = [amp_at((k + 1) * f0) for k in range(1, nharm)]
    return float(np.sqrt(np.sum(np.square(hs))) / a1 * 100.0)


def common_header(extra: str = "") -> str:
    return f"""
.title DSP Bounded Amp Suite
.param F_AUDIO={BASE_FREQ}
.param VRAIL_NOM={PARAMS['VRAIL_NOM']}
.param VBATT_NOM={PARAMS['VBATT_NOM']}
.param ETA_DC={PARAMS['ETA_DC']}
.param R_SAG={PARAMS['R_SAG']}
.param R_WIRE={PARAMS['R_WIRE']}
.param NPAR={PARAMS['NPAR']}
.param KFB=0.0028
.param KP=2.8
.param KI=450
.param UMAX=0.98
.param ILIM=110
.param ISOFT=5
.param ILIM_TOT={{ILIM*NPAR}}
.param T_AMB={PARAMS['T_AMB']}
.param T_FOLD={PARAMS['T_FOLD']}
.param T_SOFT={PARAMS['T_SOFT']}
.param RTH={PARAMS['RTH']}
.param CTH={PARAMS['CTH']}
.param PTH_SCALE={PARAMS['PTH_SCALE']}
Bvrail vrail 0 V = {{VRAIL_NOM*ETA_DC - abs(i(Vsense))*R_SAG}}
Bvcc vcc 0 V = v(vrail)
Bvee vee 0 V = -v(vrail)
{extra}
RoutA a_drv outp 0.02
RoutB b_drv outn 0.02
RwireP outp loadp {{R_WIRE/NPAR}}
RwireN outn loadn {{R_WIRE/NPAR}}
Vsense loadn loadn2 0
* load inserted per-test
Bvout vout 0 V = v(outp)-v(outn)
Berr err 0 V = v(ref) - {{KFB}}*v(vout)
Cint ui 0 1 IC=0
Rleak ui 0 1G
Gint 0 ui value = {{v(err)}}
Bu_raw uraw 0 V = {{KP}}*v(err) + {{KI}}*v(ui)
Bu_sat usat 0 V = (v(uraw)>{{UMAX}}) ? {{UMAX}} : ((v(uraw)<-{{UMAX}}) ? -{{UMAX}} : v(uraw))
Bilim flim 0 V = 0.5*(1 - tanh((abs(i(Vsense))-{{ILIM_TOT}})/{{ISOFT}}))
Cth temp 0 {{CTH}} IC={{T_AMB}}
Rth temp 0 {{RTH}}
Gheat 0 temp value = {{ abs((v(outp)-v(outn))*i(Vsense))/{{PTH_SCALE}} + (abs(i(Vsense))*abs(i(Vsense)))*R_WIRE/{{PTH_SCALE}} }}
Bftemp ftemp 0 V = 0.5*(1 - tanh((v(temp)-{{T_FOLD}})/{{T_SOFT}}))
Bu_eff ueff 0 V = v(usat)*v(flim)*v(ftemp)
Ba_drv a_drv 0 V = v(ueff) * v(vrail)
Bb_drv b_drv 0 V = -v(ueff) * v(vrail)
.options method=gear reltol=1e-4 abstol=1e-8 vntol=1e-6
"""


def test_step_load_change():
    name = "step_load_change"
    net = common_header("Vref ref 0 SIN(0 0.95 {F_AUDIO})") + r"""
Rbase loadp loadn2 1.6
Vctrl nctrl 0 PULSE(0 5 15m 1u 1u 100m 200m)
Spar loadp npar nctrl 0 SWLOAD
Rpar npar loadn2 1.6
.model SWLOAD SW(Ron=1m Roff=1e9 Vt=2.5 Vh=0.2)
.tran 10u 30m 0 10u
.meas tran P_OUT_PRE AVG par('-(v(outp)-v(outn))*i(Vsense)') from=10m to=14m
.meas tran P_OUT_POST AVG par('-(v(outp)-v(outn))*i(Vsense)') from=20m to=29m
.meas tran I_MAX MAX i(Vsense) from=0 to=30m
.control
run
set filetype=ascii
wrdata results/spice_amp_10kw_dsp_suite/step_load_change.csv time v(ref) v(vout) v(ueff) i(Vsense)
quit
.endc
.end
"""
    _, log = run_ngspice(net, name)
    m = parse_meas(log)
    return {"test": name, **m}


def test_rail_sag():
    name = "rail_sag"
    net = f"""
.title Rail Sag DSP Amp
.param F_AUDIO={BASE_FREQ}
.param VRAIL_NOM={PARAMS['VRAIL_NOM']}
.param VBATT_NOM={PARAMS['VBATT_NOM']}
.param ETA_DC={PARAMS['ETA_DC']}
.param R_SAG={PARAMS['R_SAG']}
.param R_WIRE={PARAMS['R_WIRE']}
.param KFB=0.0028
.param KP=2.8
.param KI=450
.param UMAX=0.98
.param ILIM=110
.param ISOFT=5
.param T_AMB={PARAMS['T_AMB']}
.param T_FOLD={PARAMS['T_FOLD']}
.param T_SOFT={PARAMS['T_SOFT']}
.param RTH={PARAMS['RTH']}
.param CTH={PARAMS['CTH']}
.param PTH_SCALE={PARAMS['PTH_SCALE']}
VCC vcc 0 PWL(0 100 12m 100 14m 75 20m 75 22m 100 35m 100)
VEE vee 0 PWL(0 -100 12m -100 14m -75 20m -75 22m -100 35m -100)
Vref ref 0 SIN(0 0.95 {{F_AUDIO}})
RoutA a_drv outp 0.02
RoutB b_drv outn 0.02
RwireP outp loadp {{R_WIRE}}
RwireN outn loadn {{R_WIRE}}
Vsense loadn loadn2 0
Rload loadp loadn2 1.6
Bvout vout 0 V = v(outp)-v(outn)
Berr err 0 V = v(ref) - {{KFB}}*v(vout)
Cint ui 0 1 IC=0
Rleak ui 0 1G
Gint 0 ui value = {{v(err)}}
Bu_raw uraw 0 V = {{KP}}*v(err) + {{KI}}*v(ui)
Bu_sat usat 0 V = (v(uraw)>{{UMAX}}) ? {{UMAX}} : ((v(uraw)<-{{UMAX}}) ? -{{UMAX}} : v(uraw))
Bilim flim 0 V = 0.5*(1 - tanh((abs(i(Vsense))-{{ILIM}})/{{ISOFT}}))
Cth temp 0 {{CTH}} IC={{T_AMB}}
Rth temp 0 {{RTH}}
Gheat 0 temp value = {{ abs((v(outp)-v(outn))*i(Vsense))/{{PTH_SCALE}} + (abs(i(Vsense))*abs(i(Vsense)))*R_WIRE/{{PTH_SCALE}} }}
Bftemp ftemp 0 V = 0.5*(1 - tanh((v(temp)-{{T_FOLD}})/{{T_SOFT}}))
Bu_eff ueff 0 V = v(usat)*v(flim)*v(ftemp)
Ba_drv a_drv 0 V = v(ueff) * v(vcc)
Bb_drv b_drv 0 V = -v(ueff) * v(vcc)
.options method=gear reltol=1e-4 abstol=1e-8 vntol=1e-6
.tran 10u 35m 0 10u
.meas tran P_OUT_PRE AVG par('-(v(outp)-v(outn))*i(Vsense)') from=8m to=12m
.meas tran P_OUT_POST AVG par('-(v(outp)-v(outn))*i(Vsense)') from=16m to=20m
.meas tran U_MAX MAX v(ueff) from=0 to=35m
.control
run
set filetype=ascii
wrdata results/spice_amp_10kw_dsp_suite/rail_sag.csv time v(vcc) v(vout) v(ueff) i(Vsense)
quit
.endc
.end
"""
    _, log = run_ngspice(net, name)
    m = parse_meas(log)
    return {"test": name, **m}


def test_low_impedance():
    name = "load_0p25_stability"
    net = common_header("Vref ref 0 SIN(0 0.95 {F_AUDIO})") + r"""
Rload loadp loadn2 0.25
.tran 10u 25m 0 10u
.meas tran U_MIN MIN v(ueff) from=10m to=25m
.meas tran U_MAX MAX v(ueff) from=10m to=25m
.meas tran I_POS MAX i(Vsense) from=10m to=25m
.meas tran I_NEG MIN i(Vsense) from=10m to=25m
.meas tran I_MAX PARAM='max(I_POS,-I_NEG)'
.meas tran P_OUT AVG par('-(v(outp)-v(outn))*i(Vsense)') from=10m to=25m
.control
run
set filetype=ascii
wrdata results/spice_amp_10kw_dsp_suite/load_0p25_stability.csv time v(vout) v(ueff) i(Vsense)
quit
.endc
.end
"""
    _, log = run_ngspice(net, name)
    m = parse_meas(log)
    return {"test": name, **m}


def test_hard_clipping_recovery():
    name = "hard_clipping_recovery"
    extra = r"""Bref ref 0 V = sin(2*3.14159265359*{F_AUDIO}*time) * (time<10m ? 0.6 : (time<20m ? 1.4 : 0.6))"""
    net = common_header(extra) + r"""
Rload loadp loadn2 1.6
.tran 10u 35m 0 10u
.meas tran P_OUT_CLIP AVG par('-(v(outp)-v(outn))*i(Vsense)') from=12m to=19m
.meas tran P_OUT_RECOVER AVG par('-(v(outp)-v(outn))*i(Vsense)') from=24m to=33m
.meas tran U_MAX MAX v(ueff) from=0 to=35m
.control
run
set filetype=ascii
wrdata results/spice_amp_10kw_dsp_suite/hard_clipping_recovery.csv time v(ref) v(vout) v(ueff) i(Vsense)
quit
.endc
.end
"""
    _, log = run_ngspice(net, name)
    m = parse_meas(log)
    return {"test": name, **m}


def test_thermal_foldback():
    name = "thermal_foldback"
    net = common_header("Vref ref 0 SIN(0 0.95 {F_AUDIO})") + r"""
Rload loadp loadn2 1.6
.tran 10u 60m 0 10u
.meas tran TEMP_MAX MAX v(temp) from=0 to=60m
.meas tran TEMP_END FIND v(temp) at=60m
.meas tran P_OUT_PRE AVG par('-(v(outp)-v(outn))*i(Vsense)') from=10m to=20m
.meas tran P_OUT_POST AVG par('-(v(outp)-v(outn))*i(Vsense)') from=45m to=58m
.control
run
set filetype=ascii
wrdata results/spice_amp_10kw_dsp_suite/thermal_foldback.csv time v(temp) v(vout) v(ueff) v(ftemp) i(Vsense)
quit
.endc
.end
"""
    _, log = run_ngspice(net, name)
    m = parse_meas(log)
    return {"test": name, **m}


def test_thd_vs_power():
    rows = []
    amps = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
    for amp in amps:
        name = f"thd_power_{amp:.2f}".replace(".", "p")
        net = common_header(f"Vref ref 0 SIN(0 {amp:.6f} {{F_AUDIO}})") + r"""
Rload loadp loadn2 1.6
.tran 5u 30m 0 5u
.meas tran P_OUT AVG par('-(v(outp)-v(outn))*i(Vsense)') from=10m to=30m
.control
run
set filetype=ascii
wrdata results/spice_amp_10kw_dsp_suite/""" + name + r""".csv time v(vout)
quit
.endc
.end
"""
        _, log = run_ngspice(net, name)
        m = parse_meas(log)
        traces = parse_wrdata(OUT / f"{name}.csv", ["time", "vout"])
        t = traces["time"]
        v = traces["vout"]
        # Use final 10 ms window for THD.
        mask = t >= (t.max() - 0.010)
        thd = thd_from_wave(t[mask], v[mask], BASE_FREQ, nharm=10)
        vrms = float(np.sqrt(np.mean(np.square(v[mask]))))
        rows.append(
            {
                "vref_pk": amp,
                "vout_rms": vrms,
                "p_out_w": float(m.get("p_out", float("nan"))),
                "thd_percent": thd,
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Running SPICE suite...")
    results = []
    results.append(test_step_load_change())
    results.append(test_rail_sag())
    results.append(test_low_impedance())
    results.append(test_hard_clipping_recovery())
    results.append(test_thermal_foldback())
    thd_rows = test_thd_vs_power()

    with (OUT / "suite_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        keys = sorted({k for r in results for k in r.keys()})
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(results)

    with (OUT / "thd_vs_power.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["vref_pk", "vout_rms", "p_out_w", "thd_percent"])
        w.writeheader()
        w.writerows(thd_rows)

    payload = {"tests": results, "thd_vs_power": thd_rows}
    (OUT / "suite_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# DSP Amp SPICE Validation Suite", ""]
    for r in results:
        lines.append(f"## {r['test']}")
        for k in sorted(r.keys()):
            if k == "test":
                continue
            lines.append(f"- {k}: {r[k]}")
        lines.append("")
    lines += [
        "## THD vs Power",
        f"- points: {len(thd_rows)}",
        "- csv: `results/spice_amp_10kw_dsp_suite/thd_vs_power.csv`",
        "",
        "## Artifacts",
        "- `results/spice_amp_10kw_dsp_suite/suite_metrics.csv`",
        "- `results/spice_amp_10kw_dsp_suite/thd_vs_power.csv`",
        "- `results/spice_amp_10kw_dsp_suite/suite_summary.json`",
        "- `results/spice_amp_10kw_dsp_suite/suite_report.md`",
    ]
    (OUT / "suite_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT / 'suite_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
