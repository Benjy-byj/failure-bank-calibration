#!/usr/bin/env bash
# One-command cross-family replication.
#   bash RUN_ALL.sh
# Keys are read from keys.env (edit that file first). Everything is resumable:
# rerun this same command after any interruption and it continues where it stopped.
set -uo pipefail
cd "$(dirname "$0")"

if [ ! -f keys.env ]; then
  echo "!! keys.env not found. Copy keys.env.example to keys.env and paste your keys."
  exit 1
fi
set -a; source keys.env; set +a

mkdir -p results logs
PY=${PY:-python3}
command -v "$PY" >/dev/null || PY=python

run () {  # provider model
  local prov=$1 model=$2 tag
  tag="${prov}_${model//\//-}"
  if [ -f "results/crossfam_${tag}_summary.json" ]; then
    echo "== SKIP  ${prov} / ${model}  (already summarized)"; return 0
  fi
  echo "== RUN   ${prov} / ${model}"
  if "$PY" crossfam.py --provider "$prov" --model "$model" >"logs/${tag}.log" 2>&1; then
    echo "   done -> results/crossfam_${tag}_summary.json"
  else
    echo "   FAILED (see logs/${tag}.log) — continuing with the next model"
    tail -3 "logs/${tag}.log" | sed 's/^/     /'
  fi
}

echo "### Phase 1: DeepSeek (prepaid balance)"
[ -n "${DEEPSEEK_API_KEY:-}" ] && { run deepseek deepseek-chat; run deepseek deepseek-reasoner; } || echo "   (no DEEPSEEK_API_KEY, skipping)"

echo "### Phase 2: SiliconFlow (prepaid balance)"
if [ -n "${SILICONFLOW_API_KEY:-}" ]; then
  # auto-discover available chat models, pick one Qwen + one GLM + one DeepSeek-V3-family
  "$PY" - <<'PYEOF' > results/_sf_models.txt 2>/dev/null || true
import json, os, urllib.request
req = urllib.request.Request("https://api.siliconflow.cn/v1/models",
        headers={"Authorization": "Bearer " + os.environ["SILICONFLOW_API_KEY"]})
ids = [m["id"] for m in json.loads(urllib.request.urlopen(req, timeout=60).read())["data"]]
def pick(*pats):
    for p in pats:
        c = [i for i in ids if p.lower() in i.lower() and not any(
            b in i.lower() for b in ("embedding","rerank","audio","video","image","vl","flux","bge"))]
        if c: return sorted(c, key=len)[0]
for m in filter(None, [pick("Qwen3","Qwen2.5-72B","Qwen"), pick("GLM-4","GLM"), pick("Kimi","moonshot","Yi")]):
    print(m)
PYEOF
  if [ -s results/_sf_models.txt ]; then
    while read -r m; do [ -n "$m" ] && run siliconflow "$m"; done < results/_sf_models.txt
  else
    echo "   (model discovery failed; run: $PY crossfam.py --provider siliconflow --list-models)"
  fi
else
  echo "   (no SILICONFLOW_API_KEY, skipping)"
fi

echo "### Phase 3: OpenRouter (fallback — US-lab families)"
[ -n "${OPENROUTER_API_KEY:-}" ] && { run openrouter openai/gpt-4o; run openrouter google/gemini-2.5-flash; } || echo "   (no OPENROUTER_API_KEY, skipping)"

echo
echo "########## SUMMARY ##########"
"$PY" - <<'PYEOF'
import glob, json
for f in sorted(glob.glob("results/crossfam_*_summary.json")):
    print(json.dumps(json.load(open(f))))
PYEOF
echo "########## END SUMMARY ##########"
