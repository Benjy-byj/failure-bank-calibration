#!/usr/bin/env bash
# F3: the strongest fair prompt repair — an explicit override instruction under DEAD.
# ~54 calls. bash RUN_F3.sh
set -uo pipefail; cd "$(dirname "$0")"
set -a; source keys.env; set +a
for spec in "deepseek deepseek-chat" "deepseek deepseek-reasoner" "openrouter openai/gpt-4o" \
            "openrouter google/gemini-2.5-flash" "openrouter meta-llama/llama-4-scout" \
            "openrouter mistralai/mistral-medium-3" "openrouter moonshotai/kimi-k2" \
            "openrouter z-ai/glm-4.7" "openrouter qwen/qwen3-32b"; do
  set -- $spec
  python3 crossfam_f2.py --provider "$1" --model "$2" --tasks f3 && echo "   done $2" || echo "   FAILED $2"
done
echo "########## F3 SUMMARY ##########"
python3 - <<'PYEOF'
import glob, json
for f in sorted(glob.glob("results/f2_*_summary.json")):
    d = json.load(open(f))
    if "F2_dead_override" in d: print(json.dumps(d))
PYEOF
echo "########## END ##########"
