import json, numpy as np
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
rng = np.random.default_rng(0)
S = json.load(open(_p('summary.json')))
bm, bs, nb = S['baseline']['mean'], S['baseline']['std'], S['baseline']['n']
names = list(S['verdicts'])
E = np.array([bm - S['truth'][k]['mean'] for k in names])
SE = np.array([np.sqrt(S['truth'][k]['std']**2/S['truth'][k]['n'] + bs**2/nb) for k in names])
sig = bs
# LOO empirical-prior prediction of P(wrongful | convicted) for each held-out mutation
M = 200000
loo_pred = []
for i in range(len(names)):
    prior = np.delete(E, i)
    e = rng.choice(prior, M) + rng.normal(0, SE.mean(), M)
    obs = e + rng.normal(0, sig, M)
    sel = obs <= 0
    loo_pred.append((e[sel] > 0).mean())
print(f"LOO empirical-prior W_A prediction: mean {np.mean(loo_pred):.3f} (range {min(loo_pred):.3f}-{max(loo_pred):.3f})")
print("vs in-sample MC 0.19, measured 0.175 [0.117,0.253]")
