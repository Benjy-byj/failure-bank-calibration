#!/usr/bin/env bash
# One command: choice-level provenance test (F2) on all 9 non-Claude models + qwen belief rerun.
# cd into this dir, put keys in keys.env (same format as crossfam), then: bash RUN_BEHAVIORAL_V2.sh
set -uo pipefail; cd "$(dirname "$0")"
set -a; source keys.env; set +a
run () { python3 crossfam_f2.py --provider "$1" --model "$2" ${3:-} \
         && echo "   done $2" || echo "   FAILED $2"; }
run deepseek deepseek-chat
run deepseek deepseek-reasoner
run openrouter openai/gpt-4o
run openrouter google/gemini-2.5-flash
run openrouter meta-llama/llama-4-scout
run openrouter mistralai/mistral-medium-3
run openrouter moonshotai/kimi-k2
run openrouter z-ai/glm-4.7
run openrouter qwen/qwen3-32b "--tasks all"
echo "### Phase 3: second scenario domain (drug discovery) — label effect + choice flip"
runc () { python3 crossfam_f2.py --provider "$1" --model "$2" --tasks chem \
          && echo "   done chem $2" || echo "   FAILED chem $2"; }
runc deepseek deepseek-chat
runc deepseek deepseek-reasoner
runc openrouter openai/gpt-4o
runc openrouter google/gemini-2.5-flash
runc openrouter meta-llama/llama-4-scout
runc openrouter mistralai/mistral-medium-3
runc openrouter moonshotai/kimi-k2
runc openrouter z-ai/glm-4.7
runc openrouter qwen/qwen3-32b
echo "########## SUMMARY ##########"
python3 - <<'PYEOF'
import glob, json
for f in sorted(glob.glob("results/f2_*_summary.json")): print(json.dumps(json.load(open(f))))
PYEOF
echo "########## END SUMMARY ##########"
