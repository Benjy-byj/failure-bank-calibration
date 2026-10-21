#!/usr/bin/env bash
# Apply the NegCal (calibrated-scope rendering) patch to a fresh clone of hch-wang/Negative_Knowledge.
set -euo pipefail
NK=${1:?usage: apply_patch.sh <path-to-clone>}
cp "$(dirname "$0")/patch/build_stage2.py" "$NK/reproduction/section4/scripts/build_stage2.py"
cp "$(dirname "$0")/patch/_paths.py"       "$NK/reproduction/section4/scripts/_paths.py"
echo "patched: NegCal condition added (43 entries verbatim; +status line per entry; calibrated preface)"
