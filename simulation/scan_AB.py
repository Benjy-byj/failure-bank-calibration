import json, time, numpy as np
from sim_core import sweep_s
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
B, R = 800, 80
s11 = (0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0)
out = {'w_scan': {}, 'b_scan': {}}
t0 = time.time()
for w in (40, 80, 200, 10**9):
    rows, cal = sweep_s(B, R, 1.5, s11, reps=250, seed=1, w=w)
    out['w_scan'][str(w)] = {'rows': rows.tolist(), 'cal': cal.tolist()}
    print(f"w={w} done {time.time()-t0:.0f}s")
for b in (0.0, 0.3, 0.6, 0.9):
    rows, cal = sweep_s(B, R, 1.5, s11, reps=250, seed=2, b=b)
    out['b_scan'][str(b)] = {'rows': rows.tolist(), 'cal': cal.tolist()}
    print(f"b={b} done {time.time()-t0:.0f}s")
json.dump(out, open(_p('scan_AB.json'),'w'))
for name, scan in out.items():
    print(f"\n--- {name} ---")
    for key, d in scan.items():
        r = np.array(d['rows']); g = r[:,2]; se = r[:,7]
        pk = g.argmax()
        print(f"{name[0]}={key:>10}: good s=0:{g[0]:6.1f}  peak:{g[pk]:6.1f}@s={r[pk,0]:.1f}  s=1:{g[-1]:6.1f}  (se~{se.mean():.1f})  CAL:{np.array(d['cal'])[1]:6.1f}")
