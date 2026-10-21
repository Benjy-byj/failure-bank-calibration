import json, sys, collections, numpy as np
from scipy.stats import t as tdist, norm
from itertools import combinations
def mwp(a, b):
    U = sum(x > y for x in a for y in b); pool = list(a) + list(b); n = len(a); ge = tot = 0
    for idx in combinations(range(len(pool)), n):
        aa = [pool[i] for i in idx]; bb = [pool[i] for i in range(len(pool)) if i not in idx]
        tot += 1; ge += (sum(x > y for x in aa for y in bb) >= U)
    return ge / tot
R = sys.argv[1]
D = json.load(open(f"{R}/sysloop.json")); BM, SIG, NB = D["BM"], D["SIG"], len(D["base_runs"])
runs = collections.defaultdict(list)
for l in open(f"{R}/cache.jsonl"):
    r = json.loads(l)
    if r["seed"] >= 900_000: runs[str(r["cfg"])].append((r["seed"], r["loss"]))
truth = D["truth"]; bad = 0; tr = {}
for k, m in truth.items():
    v = [x for _, x in sorted(set(runs[k]))]
    # keep the 6 seeds whose mean reproduces the stored truth
    if len(v) == 6 and abs(np.mean(v) - m) < 1e-12: tr[k] = v
    else:
        # search consecutive 6-blocks
        s = sorted(set(runs[k])); ok = False
        for i in range(len(s) - 5):
            blk = [x for _, x in s[i:i+6]]
            if abs(np.mean(blk) - m) < 1e-12: tr[k] = blk; ok = True; break
        bad += (not ok)
print(f"truth configs {len(truth)}, per-seed truth recovered {len(tr)}, unrecovered {bad}")
def disc(cfgs, crit):
    n = 0
    for c in cfgs:
        k = str(c); v = np.array(tr.get(k, []))
        m = truth[k]
        if crit == "point": n += (m < BM)
        else:
            se = np.sqrt(v.var(ddof=1) / len(v) + SIG**2 / NB)
            n += ((BM - m) / se > crit)
    return n
conds = ["nomem", "binary", "graded", "parole", "lcb"]
for name, crit in (("point (published)", "point"), ("one-sided 80%", norm.ppf(.8)), ("one-sided 90%", norm.ppf(.9)), ("one-sided 95%", norm.ppf(.95))):
    res = {c: [disc(D["state"][f"{c}-{r}"]["confirmed"], crit) for r in range(8)] for c in conds}
    g, b = res["graded"], res["binary"]
    others = [np.mean(res[c]) for c in ("nomem","binary","parole")]
    ps = {c: mwp(g, res[c]) for c in ("nomem","binary","parole","lcb")}; p = max(ps[c] for c in ("nomem","binary","parole"))
    d = np.array(g, float).mean() - np.array(b, float).mean()
    se = np.sqrt(np.var(g, ddof=1)/8 + np.var(b, ddof=1)/8); df = 14
    print(f"{name:20s} " + " ".join(f"{c}={np.mean(res[c]):.1f}" for c in conds) +
          f" | graded vs binary +{100*d/np.mean(b):.0f}%  diff {d:.1f} [95% CI {d-tdist.ppf(.975,df)*se:.1f},{d+tdist.ppf(.975,df)*se:.1f}] | p: " + " ".join(f"{c} {v:.1e}" for c, v in ps.items()))
