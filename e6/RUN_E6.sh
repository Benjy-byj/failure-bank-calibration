#!/usr/bin/env bash
# E6: second-family replication (read PREREG_E6.md). Needs OPENROUTER_API_KEY in keys.env (same as BX).
# PAR=8 runs 8 replicate loops concurrently (threads, lock-protected cache/logs): 60 loops ≈ 2–3 h instead of ~20 h. Lower PAR on 429s.
set -uo pipefail; cd "$(dirname "$0")"
set -a; source keys.env; set +a
echo "### E6 soft cell (nomem/binary/graded), GPT-4o, marginal, gated, 12 reps"
python3 llm_loop.py 150 12 --provider openrouter --model openai/gpt-4o --hard --gated --par ${PAR:-8}
echo "### E6 enforced cell (binary/graded), 12 reps"
python3 llm_loop.py 150 12 --provider openrouter --model openai/gpt-4o --hard --gated --enforce --par ${PAR:-8}
python3 e6_analysis.py | tee E6_SUMMARY.txt
echo "-> tar czf e6_results.tar.gz results/ E6_SUMMARY.txt and send it back"
