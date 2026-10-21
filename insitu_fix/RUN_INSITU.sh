#!/usr/bin/env bash
# Preregistered in-situ experiment, PARALLEL. Needs ANTHROPIC_API_KEY (+ pip install anthropic numpy scipy).
# 45 cells; with PAR=8 ≈ 6 waves × ~10 min ≈ 1 h. Lower PAR if you hit rate limits (429s in the logs).
set -uo pipefail
NK=${NK:-$HOME/Negative_Knowledge}; K=${K:-5}; KNOKB=${KNOKB:-2}; PAR=${PAR:-8}
[ -d "$NK" ] || git clone https://github.com/hch-wang/Negative_Knowledge "$NK"
HERE=$(cd "$(dirname "$0")" && pwd)
bash "$HERE/apply_patch.sh" "$NK"
cd "$NK/reproduction/section4"
python3 "$HERE/make_negcal_cells.py" || { echo "NegCal cell creation failed"; exit 1; }
export PY_VENV=${PY_VENV:-$(command -v python3)}
run_cell() {  # $1=rep $2=task $3=cond   (run_pipeline rmtree's --replay-out, so logs live beside it)
  out="runs_insitu/rep$1/$2/$3"; log="runs_insitu/rep$1/$2/$3.log"
  [ -f "$out/verified_eval.json" ] && { echo "skip $1 $2 $3"; return 0; }
  mkdir -p "runs_insitu/rep$1/$2"
  python3 run_pipeline.py --task "$2" --cond "$3" --replay-out "$out" > "$log" 2>&1 || { echo "FAILED rep$1 $2 $3 (see $log)"; return 0; }
  PYTHONPATH=scripts python3 -c "
import json, phenomenon_checks as pc
try:
    useful, diag = pc.EVALS['$2']('$out/pred_results/$2.npy')
except Exception as e:
    useful, diag = False, {'eval_error': str(e)}
json.dump({'task': '$2', 'cond': '$3', 'rep': $1, 'useful': bool(useful), 'diag': diag}, open('$out/verified_eval.json', 'w'), indent=1, default=str)
print('rep$1 $2 $3 useful=', bool(useful))"
}
export -f run_cell
for rep in $(seq 1 $K); do for task in T_A T_B T_C; do for cond in NoKB NegOnly NegCal; do [ "$cond" = NoKB ] && [ "$rep" -gt "$KNOKB" ] && continue; echo "$rep $task $cond"; done; done; done \
  | xargs -P "$PAR" -n 3 bash -c 'run_cell "$0" "$1" "$2"'
python3 "$HERE/analyze_insitu.py" runs_insitu | tee runs_insitu/SUMMARY.txt
echo "-> tar czf insitu_runs.tar.gz runs_insitu/ and send it back"
