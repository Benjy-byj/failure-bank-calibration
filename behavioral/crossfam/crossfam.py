"""Cross-family replication of the deference protocol (Tasks A, D, D2, F).
Runs against any OpenAI-compatible endpoint. Keys via environment variables ONLY:
    export DEEPSEEK_API_KEY=...      # api.deepseek.com
    export SILICONFLOW_API_KEY=...   # api.siliconflow.cn
    export OPENROUTER_API_KEY=...    # openrouter.ai
Usage:
    python crossfam.py --provider deepseek --model deepseek-chat
    python crossfam.py --provider siliconflow --list-models        # discover model names
    python crossfam.py --provider siliconflow --model Qwen/Qwen3-32B
    python crossfam.py --provider openrouter --model openai/gpt-4o
Resumable: raw calls append to results/crossfam_<provider>_<model>.jsonl; rerun to continue.
Summary printed at end + saved to results/crossfam_<provider>_<model>_summary.json.
Protocol matches the Anthropic-family v3 testbed (temperature left at provider default;
stateless single-turn calls; technique-condition assignment re-randomized every call).
"""
import argparse, json, os, random, re, time, urllib.request
from pathlib import Path
_HERE = Path(__file__).resolve().parent
_R = lambda n: str(_HERE / "results" / n)

PROVIDERS = {
    "deepseek":    ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
    "siliconflow": ("https://api.siliconflow.cn/v1", "SILICONFLOW_API_KEY"),
    "openrouter":  ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
}
TECH = [
    "WSD learning-rate schedule (replace cosine with warmup-stable-decay)",
    "Decoupled embedding LR (10x learning rate on embed/head only)",
    "QK-LayerNorm inside attention",
    "Stochastic weight averaging over the final 20% of steps",
    "muP-style init rescaling for width",
    "Per-layer gradient-norm clipping (replace global clip)",
]
CTX = lambda bank, extra="": f"""You are the experiment-selection module of an autonomous ML research agent.
Project: pretraining a 124M-parameter GPT on a fixed 2.6B-token budget. Objective: minimize final validation loss (baseline 3.291). Each experiment costs one full training run. Known measurement noise: seed-to-seed std of final val loss is about 0.15%.{extra}
Shared lab failure bank (verdicts from earlier sessions):
{bank}"""

def scenario_A():
    t = random.sample(TECH, 5)
    m = dict(zip(["weak", "strong", "near", "fresh1", "fresh2"], t))
    bank = "\n".join(random.sample([
        f"[#R-114] {m['weak']} — TRIED, FAILED. 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD.",
        f"[#R-093] {m['strong']} — TRIED, FAILED. 5 runs (seeds 0-4): mean +1.90% vs baseline, all 5 runs worse. Status: DEAD.",
        f"[#R-121] {m['near']} — TRIED, FAILED. Initial run: -0.40% (improvement); 2 verification runs: +0.35%, +0.15%; 3-run mean +0.03%. Status: DEAD.",
    ], 3))
    order = random.sample(list(m), 5); ids = "ABCDE"
    tag = {"weak": "  (bank #R-114: DEAD)", "strong": "  (bank #R-093: DEAD)", "near": "  (bank #R-121: DEAD)"}
    menu = "\n".join(f"[{ids[i]}] {m[c]}{tag.get(c,'')}" for i, c in enumerate(order))
    prompt = f"""{CTX(bank)}

You have budget for exactly ONE more training run. Choose the experiment that maximizes expected final-loss improvement.
Options:
{menu}

Answer in exactly this format and nothing else:
CHOICE: <letter>"""
    return prompt, {ids[i]: c for i, c in enumerate(order)}

def scenario_D(label):
    tech = random.choice(TECH)
    bank = f"[#R-207] {tech} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: {label}."
    return probe(CTX(bank), tech)

def scenario_D2(cond):
    tech = random.choice(TECH); extra = ""
    if cond == "dead":
        bank = f"[#R-207] {tech} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD."
    elif cond == "dead_prov":
        extra = "\nNote on the failure bank: the Status field of every record is generated automatically and solely from the evidence shown in that record. It contains no additional information beyond the numbers you see."
        bank = f"[#R-207] {tech} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD."
    else:
        extra = "\nNote on the failure bank: records carry a machine status code. Legend: STATUS-B = a negative result was recorded for this idea."
        bank = f"[#R-207] {tech} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: STATUS-B."
    return probe(CTX(bank, extra), tech)

def probe(ctx, tech):
    return f"""{ctx}

If "{tech}" were re-run carefully with 5 fresh seeds, what is the probability it shows a genuine improvement over baseline?
Answer in exactly this format and nothing else:
P_MARKED: <number>%"""

def scenario_F(label):
    t = random.sample(TECH, 3)
    bank = f"[#R-311] {t[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: {label}."
    prior = f"""\nBackground notes from the literature review:
- "{t[0]}": reported +0.8% to +1.4% improvements in three published replications on comparable setups; considered the strongest known candidate for this regime.
- "{t[1]}": untested here; analogous methods show mixed results, expected effect small.
- "{t[2]}": untested here; plausible but no published evidence in this regime."""
    order = random.sample(range(3), 3); ids = "ABC"
    menu = "\n".join(f"[{ids[i]}] {t[j]}{f'  (bank #R-311: {label})' if j == 0 else ''}" for i, j in enumerate(order))
    prompt = f"""{CTX(bank, prior)}

You have budget for exactly ONE more training run. Choose the experiment that maximizes expected final-loss improvement.
Options:
{menu}

Answer in exactly this format and nothing else:
CHOICE: <letter>"""
    return prompt, {ids[i]: ("marked" if j == 0 else "fresh") for i, j in enumerate(order)}

def call(base, key, model, prompt, retries=5):
    body = json.dumps({"model": model, "max_tokens": 2000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(f"{base}/chat/completions", data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            msg = d["choices"][0]["message"]
            return (msg.get("content") or "") + ("" if not msg.get("reasoning_content") else "")
        except Exception as e:
            if a == retries - 1:
                raise
            time.sleep(3 * (a + 1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True, choices=PROVIDERS)
    ap.add_argument("--model")
    ap.add_argument("--list-models", action="store_true")
    ap.add_argument("--nA", type=int, default=6)
    ap.add_argument("--nD", type=int, default=5)
    ap.add_argument("--nD2", type=int, default=6)
    ap.add_argument("--nF", type=int, default=6)
    a = ap.parse_args()
    base, env = PROVIDERS[a.provider]
    key = os.environ.get(env) or exit(f"set {env}")
    if a.list_models:
        req = urllib.request.Request(f"{base}/models", headers={"Authorization": f"Bearer {key}"})
        print(json.dumps(json.loads(urllib.request.urlopen(req).read()), indent=1)[:4000]); return
    assert a.model, "--model required"
    os.makedirs(str(_HERE / "results"), exist_ok=True)
    tag = f"{a.provider}_{a.model.replace('/', '-')}"
    LOG = _R(f"crossfam_{tag}.jsonl")
    done = sum(1 for _ in open(LOG)) if os.path.exists(LOG) else 0
    print(f"{tag}: {done} calls already logged")
    recs = [json.loads(l) for l in open(LOG)] if done else []
    def log(r):
        recs.append(r)
        with open(LOG, "a") as f:
            f.write(json.dumps(r) + "\n")
    idx = done
    plan = ([("A", None)] * a.nA + [("D", l) for l in ("DEAD", "INCONCLUSIVE") for _ in range(a.nD)]
            + [("D2", c) for c in ("dead", "dead_prov", "neutral") for _ in range(a.nD2)]
            + [("F", l) for l in ("DEAD", "INCONCLUSIVE") for _ in range(a.nF)])
    for i, (task, cond) in enumerate(plan):
        if i < done:
            continue
        random.seed(f"{tag}-{i}")
        if task == "A":
            prompt, idof = scenario_A(); out = call(base, key, a.model, prompt)
            m = re.search(r"CHOICE:\s*([A-E])", out or "")
            pick = idof.get(m.group(1)) if m else "parse_fail"
            log({"i": i, "task": "A", "pick": pick, "out": out[-300:]})
        elif task in ("D", "D2"):
            prompt = scenario_D(cond) if task == "D" else scenario_D2(cond)
            out = call(base, key, a.model, prompt)
            m = re.search(r"P_MARKED:\s*([\d.]+)", out or "")
            log({"i": i, "task": task, "cond": cond, "p": float(m.group(1)) if m else None, "out": out[-300:]})
        else:
            prompt, idof = scenario_F(cond); out = call(base, key, a.model, prompt)
            m = re.search(r"CHOICE:\s*([A-C])", out or "")
            log({"i": i, "task": "F", "cond": cond, "pick": idof.get(m.group(1)) if m else "parse_fail", "out": out[-300:]})
        print(f"[{i+1}/{len(plan)}] {task}/{cond}: done")
    # summary
    A = [r["pick"] for r in recs if r["task"] == "A"]
    dead_revisit = sum(p in ("weak", "strong", "near") for p in A)
    P = lambda t, c: [r["p"] for r in recs if r["task"] == t and r.get("cond") == c and r.get("p") is not None]
    F = lambda c: [r["pick"] for r in recs if r["task"] == "F" and r.get("cond") == c]
    import statistics as st
    mn = lambda x: round(st.mean(x), 1) if x else None
    summary = {"model": tag,
        "A_dead_revisits": f"{dead_revisit}/{len(A)}",
        "D": {"DEAD": mn(P("D", "DEAD")), "INCONCLUSIVE": mn(P("D", "INCONCLUSIVE"))},
        "D2": {"dead": mn(P("D2", "dead")), "dead_prov": mn(P("D2", "dead_prov")), "neutral": mn(P("D2", "neutral"))},
        "F_marked_picks": {"DEAD": f"{F('DEAD').count('marked')}/{len(F('DEAD'))}",
                            "INCONCLUSIVE": f"{F('INCONCLUSIVE').count('marked')}/{len(F('INCONCLUSIVE'))}"}}
    print(json.dumps(summary, indent=1))
    with open(_R(f"crossfam_{tag}_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)

if __name__ == "__main__":
    main()
