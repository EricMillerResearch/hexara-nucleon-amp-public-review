#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/5] Checking required files..."
required=(
  "SHA256SUMS"
  "RUN_METADATA.json"
  "requirements.lock"
  "scripts/run_spice_amp_validation_suite.py"
)
for f in "${required[@]}"; do
  [[ -f "$f" ]] || { echo "Missing required file: $f"; exit 1; }
done

echo "[2/5] Checking required tools..."
command -v python3 >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }
command -v shasum >/dev/null 2>&1 || { echo "shasum not found"; exit 1; }
if ! command -v ngspice >/dev/null 2>&1; then
  echo "ngspice not found (hash verification still possible, reruns will fail without it)."
fi

echo "[3/5] Verifying file hashes..."
shasum -a 256 -c SHA256SUMS

echo "[4/5] Reporting environment versions..."
python3 - << 'PY'
import json, subprocess, sys
from pathlib import Path

meta = json.loads(Path("RUN_METADATA.json").read_text(encoding="utf-8"))

def get(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
        return out
    except Exception:
        return "UNAVAILABLE"

py = sys.version.split()[0]
np = "UNAVAILABLE"
try:
    import numpy as _np
    np = _np.__version__
except Exception:
    pass

ng = get(["ngspice", "-v"]).splitlines()[1].strip() if get(["ngspice", "-v"]) != "UNAVAILABLE" else "UNAVAILABLE"

print("Recorded:")
print(f"  python_version: {meta.get('python_version')}")
print(f"  numpy_version:  {meta.get('numpy_version')}")
print(f"  ngspice_version:{meta.get('ngspice_version')}")
print("Current:")
print(f"  python_version: {py}")
print(f"  numpy_version:  {np}")
print(f"  ngspice_version:{ng}")
PY

echo "[5/5] Verification completed successfully."
echo "Tip: for full reproducibility rerun: python3 scripts/run_spice_amp_validation_suite.py"
