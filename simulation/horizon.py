import numpy as np, json, time
import sys; sys.path.insert(0,'failure-bank')
from robust import run_once

import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
def batch(reps, seed, **kw):
    rng = np.random.default_rng(seed)
    v = np.array([run_once(rng, **kw) for _ in range(reps)])
    return v.mean(0)

# extinction prob single-type approx: q = (1-p) + p q^C, p = lambda/C
def q_ext(lam, C=3):
    p = lam/C
    q = 0.5
    for _ in range(200): q = (1-p) + p*q**C
    return q

LAM = json.load(open(_p('lambda.json')))
cells = [(1.5,0.6), (2.0,0.9), (1.0,0.9)]
Bs = [200,400,800,1600,3200]
s6 = (0,.3,.5,.7,.85,1.0)
out = {}
t0=time.time()
for sig,b in cells:
    lam = LAM[f"{sig}|{b}"]
    depths=[]
    for B in Bs:
        reps = 160 if B<=1600 else 100
        gs=[batch(reps, 23, B=B, R=80, sigma=sig, policy='naive', s=s, b=b)[1] for s in s6]
        gs=np.array(gs); depths.append((gs.max()-gs[-1])/gs.max()*100)
    out[f"{sig}|{b}"]={'lam':lam,'q':q_ext(lam),'Bs':Bs,'depths':depths}
    print(f"cell ({sig},{b}) lam={lam:.3f} q_ext={q_ext(lam):.3f} depths={np.round(depths,1)}  [{time.time()-t0:.0f}s]", flush=True)
json.dump(out, open(_p('horizon.json'),'w'))
