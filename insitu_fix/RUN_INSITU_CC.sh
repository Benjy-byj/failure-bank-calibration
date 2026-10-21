#!/usr/bin/env bash
# In-situ experiment via CLAUDE CODE (your subscription; no API key). Mirrors how the authors ran their
# own stage-2 cells (meta.json tools_allowed = Read/Write/Bash). Needs: `claude` CLI logged in, python3 with
# numpy+scipy. Each cell runs headless in its own throwaway directory.
set -uo pipefail
NK=${NK:-$HOME/Negative_Knowledge}; K=${K:-5}; KNOKB=${KNOKB:-2}; PAR=${PAR:-3}; MODEL=${MODEL:-sonnet}
HERE=$(cd "$(dirname "$0")" && pwd)
[ -d "$NK" ] || git clone https://github.com/hch-wang/Negative_Knowledge "$NK"
bash "$HERE/apply_patch.sh" "$NK"
cd "$NK/reproduction/section4"
python3 "$HERE/make_negcal_cells.py" || { echo "NegCal cell creation failed"; exit 1; }
PY=$(command -v python3); export PY S4="$PWD" MODEL
run_cell() {  # $1=rep $2=task $3=cond
  cell="$S4/logs/stage2/$2/$3"; out="$S4/runs_insitu/rep$1/$2/$3"; log="$S4/runs_insitu/rep$1/$2/$3.log"
  [ -f "$out/verified_eval.json" ] && { echo "skip $1 $2 $3"; return 0; }
  rm -rf "$out"; mkdir -p "$out/pred_results"; cp "$cell/memory.md" "$out/" 2>/dev/null || true
  # localize the authors' absolute paths — identically for every condition
  sed -e "s#/Users/dietcoke/[^[:space:]\`)]*bank_v3A_negative\.jsonl#$out/memory.md#g" \
      -e "s#/Users/dietcoke/[^[:space:]\`)]*bank_v3A_positive\.jsonl#$out/memory.md#g" \
      -e "s#/Users/dietcoke/[^[:space:]\`)]*/runs/$2/[A-Za-z]*#$out#g" \
      -e "s#/Users/dietcoke/[^[:space:]\`)]*/bin/python#$PY#g" "$cell/prompt.md" > "$out/prompt.md"
  ( cd "$out" && claude -p "$(cat prompt.md)" --model "$MODEL" --max-turns 80 --dangerously-skip-permissions ) > "$log" 2>&1 \
    || { echo "FAILED rep$1 $2 $3 (see $log)"; return 0; }
  PYTHONPATH="$S4/scripts" python3 - "$1" "$2" "$3" "$out" << 'PYEOF'
import json, sys, phenomenon_checks as pc
rep, task, cond, out = sys.argv[1:5]
try:
    useful, diag = pc.EVALS[task](f"{out}/pred_results/{task}.npy")
except Exception as e:
    useful, diag = False, {"eval_error": str(e)}
json.dump({"task": task, "cond": cond, "rep": int(rep), "useful": bool(useful), "diag": diag}, open(f"{out}/verified_eval.json", "w"), indent=1, default=str)
print(f"rep{rep} {task} {cond} useful={bool(useful)}")
PYEOF
}
export -f run_cell
for rep in $(seq 1 $K); do for task in T_A T_B T_C; do for cond in NoKB NegOnly NegCal; do
  [ "$cond" = NoKB ] && [ "$rep" -gt "$KNOKB" ] && continue; echo "$rep $task $cond"; done; done; done \
  | xargs -P "$PAR" -n 3 bash -c 'run_cell "$0" "$1" "$2"'
python3 "$HERE/analyze_insitu.py" runs_insitu | tee runs_insitu/SUMMARY.txt
echo "-> cd $S4 && tar czf ~/insitu_runs.tar.gz runs_insitu/   (then upload insitu_runs.tar.gz)"
