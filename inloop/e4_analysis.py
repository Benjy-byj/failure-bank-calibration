"""E4 analysis: success-gated LLM proposer, marginal cell.
Usage: python3 e4_analysis.py   (from this dir, after the gated run)
Reports per condition: truth-validated discoveries, wrongful convictions in the bank,
rescued good ideas, gate compliance, and the flat-vs-gated contrast against E1-hard.
"""
import json, glob, os
import numpy as np
R = "results"
J = json.load(open(f"{R}/llm_loop_deepseek_deepseek-chat_hard_gated.json"))
BM, SIG, truth = J["BM"], J["SIG"], J["truth"]
effs = {k: (BM - v)/SIG for k, v in truth.items()}
print(f"baseline {BM:.4f}±{SIG:.4f}; {len(truth)} distinct proposals truth-tested")
print(f"{'cond':8s}{'rep':4s}{'disc':6s}{'gate_rej':9s}{'records':8s}{'wrongful':9s}{'rescued':8s}")
summary = {}
for cond in ("nomem","binary","graded"):
    ds = []
    for f in sorted(glob.glob(f"{R}/llm_state_deepseek_deepseek-chat_hard_gated_{cond}_*.json")):
        st = json.load(open(f))
        conf, recs = set(st["confirmed"]), st["records"]
        disc = sum(effs.get(c, -9) > 0 for c in conf)
        wr = sum(1 for k in recs if effs.get(k, -9) > 0 and k not in conf)
        resc = sum(1 for k in recs if k in conf and effs.get(k, -9) > 0)
        rep = f.rsplit("_", 1)[1].split(".")[0]
        print(f"{cond:8s}{rep:4s}{disc:<6d}{st.get('gate_rejects',0):<9d}{len(recs):<8d}{wr:<9d}{resc:<8d}")
        ds.append(disc)
    summary[cond] = ds
print()
for cond, ds in summary.items():
    print(f"{cond:8s}: discoveries {ds}  mean {np.mean(ds):.1f}  sd {np.std(ds, ddof=1):.1f}")
if all(len(v) >= 3 for v in summary.values()):
    from itertools import combinations
    def mw(a, b):
        U = sum(x > y for x in a for y in b)
        pool = a + b; n = len(a); ge = tot = 0
        for idx in combinations(range(len(pool)), n):
            aa = [pool[i] for i in idx]; bb = [pool[i] for i in range(len(pool)) if i not in idx]
            tot += 1; ge += (sum(x > y for x in aa for y in bb) >= U)
        return ge / tot
    g = summary["graded"]
    for c in ("nomem", "binary"):
        print(f"graded vs {c}: exact one-sided rank p = {mw(g, summary[c]):.4f}")
print("\nFlat-vs-gated contrast (same cell): E1-hard flat means were 18.7/19.3/19.7 (none/binary/graded).")
print("Send back this output + the results/ dir.")
