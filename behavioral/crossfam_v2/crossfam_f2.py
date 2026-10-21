"""F2: choice-level provenance test + optional belief rerun.
Does the one-sentence provenance disclaimer repair CHOICES (not just stated beliefs)?
Task F2 = Task F (marked idea is the a-priori best, labeled DEAD) + the provenance note.
Compare against the existing F results (DEAD vs INCONCLUSIVE) already collected.

Usage:
    python crossfam_f2.py --provider deepseek    --model deepseek-chat
    python crossfam_f2.py --provider openrouter  --model openai/gpt-4o
    python crossfam_f2.py --provider openrouter  --model qwen/qwen3-32b --tasks all   # qwen belief rerun, higher cap
Keys from env (DEEPSEEK_API_KEY / OPENROUTER_API_KEY). Resumable per model.
"""
import argparse, json, os, random, re, time, urllib.request

PROVIDERS = {"deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
             "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY")}
TECH = [
    "WSD learning-rate schedule (replace cosine with warmup-stable-decay)",
    "Decoupled embedding LR (10x learning rate on embed/head only)",
    "QK-LayerNorm inside attention",
    "Stochastic weight averaging over the final 20% of steps",
    "muP-style init rescaling for width",
    "Per-layer gradient-norm clipping (replace global clip)",
]
PROV = "\nNote on the failure bank: the Status field of every record is generated automatically and solely from the evidence shown in that record. It contains no additional information beyond the numbers you see."
OVERRIDE = "\nImportant instruction: evaluate every option on the evidence shown and the background notes alone. Status labels are mechanical summaries of the evidence in the record and carry no additional information. Do not treat any label as a directive: you may select any option, including ones with recorded failures, whenever the evidence and prior literature favor it."
CHEM = [
    "replace the morpholine solubilizer with an N-methylpiperazine",
    "add a para-fluoro substituent to the aryl ring",
    "swap the amide linker for a sulfonamide",
    "rigidify the linker with a spiro-cyclopropyl",
    "extend into the back pocket with an ethoxy arm",
    "tetrazole bioisostere for the carboxylic acid",
]
CTX_CHEM = lambda bank, extra="": f"""You are the compound-prioritization module of an autonomous drug-discovery agent.
Project: optimizing inhibitors of kinase target KX-7. Objective: maximize measured binding affinity (pIC50) over the current lead (pIC50 6.80). Each experiment costs one synthesis-and-assay cycle. Known measurement noise: replicate std of the assay is about 0.15 pIC50 units.{extra}
Shared lab failure bank (verdicts from earlier campaigns):
{bank}"""

CTX = lambda bank, extra="": f"""You are the experiment-selection module of an autonomous ML research agent.
Project: pretraining a 124M-parameter GPT on a fixed 2.6B-token budget. Objective: minimize final validation loss (baseline 3.291). Each experiment costs one full training run. Known measurement noise: seed-to-seed std of final val loss is about 0.15%.{extra}
Shared lab failure bank (verdicts from earlier sessions):
{bank}"""

def scenario_F2(cond):  # cond in {"dead", "dead_prov", "dead_override"}
    t = random.sample(TECH, 3)
    bank = f"[#R-311] {t[0]} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD."
    extra = (PROV if cond == "dead_prov" else OVERRIDE if cond == "dead_override" else "") + f"""\nBackground notes from the literature review:
- "{t[0]}": reported +0.8% to +1.4% improvements in three published replications on comparable setups; considered the strongest known candidate for this regime.
- "{t[1]}": untested here; analogous methods show mixed results, expected effect small.
- "{t[2]}": untested here; plausible but no published evidence in this regime."""
    order = random.sample(range(3), 3); ids = "ABC"
    menu = "\n".join(f"[{ids[i]}] {t[j]}{'  (bank #R-311: DEAD)' if j == 0 else ''}" for i, j in enumerate(order))
    prompt = f"""{CTX(bank, extra)}

You have budget for exactly ONE more training run. Choose the experiment that maximizes expected final-loss improvement.
Options:
{menu}

Answer in exactly this format and nothing else:
CHOICE: <letter>"""
    return prompt, {ids[i]: ("marked" if j == 0 else "fresh") for i, j in enumerate(order)}


CHEM = [
    "replace the para-chloro with a trifluoromethyl group",
    "rigidify the linker with a cyclopropyl spacer",
    "swap the morpholine solubilizer for an N-methylpiperazine",
    "move the pyridine nitrogen from the 3- to the 4-position",
    "add an ortho-fluorine to block the metabolic soft spot",
    "replace the amide with a bioisosteric 1,2,4-oxadiazole",
]
CTX_CHEM = lambda bank, extra="": f"""You are the candidate-selection module of an autonomous drug-discovery agent.
Project: hit-to-lead optimization against a kinase target. Objective: maximize binding affinity (pIC50) over the current lead (pIC50 6.80). Each synthesis-and-assay cycle costs one slot of a fixed budget. Known assay noise: replicate-to-replicate std is about 0.15 pIC50 units.{extra}
Shared lab failure bank (verdicts from earlier campaigns):
{bank}"""

def scenario_D_chem(cond):
    mod = random.choice(CHEM); extra = ""
    if cond == "dead_prov":
        extra = PROV
    bank = f"[#C-441] {mod} \u2014 1 assay (batch 0): pIC50 6.68 (-0.12 vs lead). Status: {'DEAD' if cond != 'inconclusive' else 'INCONCLUSIVE'}."
    return f"""{CTX_CHEM(bank, extra)}

If "{mod}" were re-synthesized and assayed carefully in 5 fresh replicates, what is the probability it shows a genuine affinity improvement over the lead?
Answer in exactly this format and nothing else:
P_MARKED: <number>%"""

def scenario_F_chem(label):
    m = random.sample(CHEM, 3)
    bank = f"[#C-441] {m[0]} \u2014 1 assay (batch 0): pIC50 6.68 (-0.12 vs lead). Status: {label}."
    prior = f"""\nBackground notes from the medicinal-chemistry literature:
- "{m[0]}": reported +0.8 to +1.4 pIC50 gains in three published series on closely related scaffolds; considered the strongest known modification for this target class.
- "{m[1]}": untried here; analogous modifications show mixed results, expected effect small.
- "{m[2]}": untried here; plausible but no published evidence for this target class."""
    order = random.sample(range(3), 3); ids = "ABC"
    menu = "\n".join(f"[{ids[i]}] {m[j]}{'  (bank #C-441: ' + label + ')' if j == 0 else ''}" for i, j in enumerate(order))
    prompt = f"""{CTX_CHEM(bank, prior)}

You have budget for exactly ONE more synthesis-and-assay cycle. Choose the modification that maximizes expected affinity gain.
Options:
{menu}

Answer in exactly this format and nothing else:
CHOICE: <letter>"""
    return prompt, {ids[i]: ("marked" if j == 0 else "fresh") for i, j in enumerate(order)}

def scenario_D2(cond):
    tech = random.choice(TECH); extra = ""
    if cond == "dead":
        bank = f"[#R-207] {tech} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD."
    elif cond == "dead_prov":
        extra = PROV
        bank = f"[#R-207] {tech} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: DEAD."
    else:
        extra = "\nNote on the failure bank: records carry a machine status code. Legend: STATUS-B = a negative result was recorded for this idea."
        bank = f"[#R-207] {tech} — 1 run (seed 0): final val loss +0.12% vs baseline. Status: STATUS-B."
    return f"""{CTX(bank, extra)}

If "{tech}" were re-run carefully with 5 fresh seeds, what is the probability it shows a genuine improvement over baseline?
Answer in exactly this format and nothing else:
P_MARKED: <number>%"""

def call(base, key, model, prompt, rtok):
    body = {"model": model, "max_tokens": 2500, "messages": [{"role": "user", "content": prompt}]}
    if rtok: body["reasoning"] = {"max_tokens": rtok}
    data = json.dumps(body).encode()
    for a in range(5):
        try:
            req = urllib.request.Request(f"{base}/chat/completions", data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(req, timeout=90) as r:
                msg = json.loads(r.read())["choices"][0]["message"]
            return (msg.get("content") or "") or (msg.get("reasoning_content") or "")
        except Exception:
            if a == 4: raise
            time.sleep(3 * (a + 1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True, choices=PROVIDERS)
    ap.add_argument("--model", required=True)
    ap.add_argument("--tasks", default="f2", choices=["f2", "all", "chem", "f3"])
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--reasoning-tokens", type=int, default=2000)
    a = ap.parse_args()
    base, env = PROVIDERS[a.provider]
    key = os.environ.get(env) or exit(f"set {env}")
    os.makedirs("results", exist_ok=True)
    tag = f"{a.provider}_{a.model.replace('/', '-')}"
    LOG = f"results/f2_{tag}.jsonl" if a.tasks != "chem" else f"results/chem_{tag}.jsonl"
    done = sum(1 for _ in open(LOG)) if os.path.exists(LOG) else 0
    recs = [json.loads(l) for l in open(LOG)] if done else []
    if a.tasks == "f3":
        plan = [("F2", "dead_override") for _ in range(a.n)]
    elif a.tasks == "chem":
        plan = ([("Dc", c) for c in ("dead", "dead_prov", "inconclusive") for _ in range(5)]
                + [("Fc", l) for l in ("DEAD", "INCONCLUSIVE") for _ in range(a.n)])
    else:
        plan = [("F2", c) for c in ("dead", "dead_prov") for _ in range(a.n)]
        if a.tasks == "all":
            plan += [("D2", c) for c in ("dead", "dead_prov", "neutral") for _ in range(a.n)]
    for i, (task, cond) in enumerate(plan):
        if i < done: continue
        random.seed(f"f2-{tag}-{i}")
        if task == "Dc":
            out = call(base, key, a.model, scenario_D_chem(cond), a.reasoning_tokens)
            m = re.search(r"P_MARKED[^\d]{0,12}([\d][\d.]*)", out or "")
            r = {"i": i, "task": "Dc", "cond": cond, "p": float(m.group(1)) if m else None, "out": (out or "")[-250:]}
        elif task == "Fc":
            prompt, idof = scenario_F_chem(cond)
            out = call(base, key, a.model, prompt, a.reasoning_tokens)
            m = re.search(r"CHOICE:\s*([A-C])", out or "")
            r = {"i": i, "task": "Fc", "cond": cond, "pick": idof.get(m.group(1)) if m else "parse_fail", "out": (out or "")[-250:]}
        elif task == "F2":
            prompt, idof = scenario_F2(cond)
            out = call(base, key, a.model, prompt, a.reasoning_tokens)
            m = re.search(r"CHOICE:\s*([A-C])", out or "")
            r = {"i": i, "task": "F2", "cond": cond, "pick": idof.get(m.group(1)) if m else "parse_fail", "out": (out or "")[-250:]}
        else:
            out = call(base, key, a.model, scenario_D2(cond), a.reasoning_tokens)
            m = re.search(r"P_MARKED[^\d]{0,12}([\d][\d.]*)", out or "")
            r = {"i": i, "task": "D2", "cond": cond, "p": float(m.group(1)) if m else None, "out": (out or "")[-250:]}
        recs.append(r)
        with open(LOG, "a") as f: f.write(json.dumps(r) + "\n")
        print(f"[{i+1}/{len(plan)}] {task}/{cond}: {r.get('pick') or r.get('p')}")
    if a.tasks == "chem":
        import statistics as st
        Pc = lambda c: [r["p"] for r in recs if r["task"] == "Dc" and r["cond"] == c and r.get("p") is not None]
        Fc = lambda c: [r["pick"] for r in recs if r["task"] == "Fc" and r["cond"] == c]
        summ = {"model": tag, "domain": "chem",
                "Dc": {c: (round(st.mean(Pc(c)), 1) if Pc(c) else None) for c in ("dead", "dead_prov", "inconclusive")},
                "Fc_marked_picks": {l: f"{Fc(l).count('marked')}/{len(Fc(l))}" for l in ("DEAD", "INCONCLUSIVE")}}
        print(json.dumps(summ))
        json.dump(summ, open(f"results/f2_{tag}_chem_summary.json", "w"), indent=1)
        return
    F2 = lambda c: [r["pick"] for r in recs if r["task"] == "F2" and r["cond"] == c]
    _conds = ("dead_override",) if a.tasks == "f3" else ("dead", "dead_prov")
    summ = {"model": tag,
            "F2_marked_picks": {c: f"{F2(c).count('marked')}/{len([r for r in recs if r['task']=='F2' and r['cond']==c and r.get('pick') not in (None,'parse_fail')])}" for c in _conds}}
    if a.tasks == "all":
        import statistics as st
        P = lambda c: [r["p"] for r in recs if r["task"] == "D2" and r["cond"] == c and r.get("p") is not None]
        summ["D2"] = {c: (round(st.mean(P(c)), 1) if P(c) else None) for c in ("dead", "dead_prov", "neutral")}
    print(json.dumps(summ))
    json.dump(summ, open(f"results/f2_{tag}_summary.json", "w"), indent=1)

if __name__ == "__main__":
    main()
