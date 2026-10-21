import json, numpy as np
from scipy.special import ndtr
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
rng = np.random.default_rng(0)
recs = [json.loads(l) for l in open(_p('log.jsonl'))]
D = {}
for r in recs: D[(r['phase'], r['name'], r['seed'])] = r['loss']
base = [v for (p,n,s),v in D.items() if p=='baseline']
bm, bs = float(np.mean(base)), float(np.std(base, ddof=1))
names = sorted({n for (p,n,s) in D if p=='verdict'})
truth = {k: [v for (p,n,s),v in D.items() if p=='truth' and n==k] for k in names}
eff = {k: bm - np.mean(truth[k]) for k in names}
se  = {k: np.sqrt(np.var(truth[k], ddof=1)/len(truth[k]) + bs**2/len(base)) for k in names}
E = np.array([eff[k] for k in names])
print(f"DOMAIN 2 (MLP/digits): baseline {bm:.4f}±{bs:.4f}(n={len(base)}); tau {E.std(ddof=1):.4f}; sigma/tau {bs/E.std(ddof=1):.2f}; good ideas {sum(E>0)}/{len(names)}")
fails, vfails, confs = [], [], []
vseed = {n: s for (p_,n,s) in D if p_=='verdict'}
wseed = {}
for (p_,n,s) in D:
    if p_=='verify': wseed.setdefault(n, []).append(s)
for i,k in enumerate(names):
    v = D[('verdict',k,vseed[k])]
    if v >= bm: fails.append(k); continue
    m3 = np.mean([v] + [D[('verify',k,s)] for s in sorted(wseed.get(k, []))[:2]])
    (confs if m3 < bm else vfails).append(k)
wA = [k for k in fails if eff[k] > 0]
wB = [k for k in vfails if eff[k] > 0]
fc = [k for k in confs if eff[k] <= 0]
awA = sum(ndtr(eff[k]/se[k]) for k in fails)/max(1,len(fails))
awB = sum(ndtr(eff[k]/se[k]) for k in vfails)/max(1,len(vfails))
print(f"single-shot convictions: {len(fails)}, wrongful {len(wA)} -> W_A {len(wA)/len(fails):.2f} (aware {awA:.2f}) | {wA}")
print(f"verification convictions: {len(vfails)}, wrongful {len(wB)} -> W_B {len(wB)/max(1,len(vfails)):.2f} (aware {awB:.2f}) | {wB}")
print(f"confirmed {len(confs)}, false confirms {len(fc)} | {fc}")
print(f"wrongful effects (sigma units): {[round(eff[k]/bs,2) for k in wA]}")
# theory: LOO empirical-prior MC
M = 200000; preds = []
for i in range(len(names)):
    prior = np.delete(E, i)
    e = rng.choice(prior, M) + rng.normal(0, np.mean([se[k] for k in names]), M)
    obs = e + rng.normal(0, bs, M)
    s1 = obs <= 0; preds.append((e[s1] > 0).mean())
e = rng.choice(E, M) + rng.normal(0, np.mean([se[k] for k in names]), M)
x1 = e + rng.normal(0, bs, M); vsum = x1 + rng.normal(0, bs, M) + rng.normal(0, bs, M)
selB = (x1 < 0)==False; selB = (x1 <= 0)^True  # x1>0
selB = (x1 > 0) & (vsum/3 > 0)^True & (x1>0)
selB = (x1 > 0) & ((vsum/3) <= 0)
print(f"theory W_A (LOO empirical prior): {np.mean(preds):.3f} | theory W_B (in-sample): {(e[selB]>0).mean():.3f}")
