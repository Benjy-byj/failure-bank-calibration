# Cross-family deference replication — one command

## 1. Put your keys in place
    cp keys.env.example keys.env
    nano keys.env          # paste the three keys

## 2. Run everything
    bash RUN_ALL.sh

That's it. It runs DeepSeek (chat + reasoner), auto-discovers and runs 3 SiliconFlow models
(a Qwen, a GLM, one more), then OpenRouter (gpt-4o, gemini) if that key is set.
~52 short calls per model. Resumable and idempotent: if it dies, or you Ctrl-C, just run
`bash RUN_ALL.sh` again — finished models are skipped, partial models continue mid-way.
A model that errors out does not stop the others.

Prefer to background it:
    nohup bash RUN_ALL.sh > run_all.log 2>&1 &
    tail -f run_all.log

## 3. Output
Per-model summaries are written to `results/*_summary.json`; full per-call records
land in `results/*.jsonl`. The run also prints a consolidated summary block.

## Notes
- Only needs python3 with the standard library (urllib) — no pip installs.
- Protocol is verbatim-identical to the Anthropic-family v3 testbed (Tasks A/D/D2/F).
