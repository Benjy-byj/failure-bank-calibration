import numpy as np
from scipy.special import ndtr

import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
def run_once(rng, B, R, mu0, tau, sigma, policy, s=None,
             v_verify=2, C=3, a=-0.6, b=0.6, tau_c=0.8, w=80):
    cap = B * (1 + C) + R + 8
    delta = np.empty(cap); n_fail = np.zeros(cap, np.int32)
    locked = np.zeros(cap, bool); confirmed = np.zeros(cap, bool)
    sum_obs = np.zeros(cap); n_obs = np.zeros(cap, np.int32)
    delta[:R] = rng.normal(mu0, tau, R); N = R
    prec0 = 1.0 / tau**2
    value = 0.0; n_good = 0; n_bad = 0; n_retry = 0; n_wl = 0
    t = 0
    while t < B:
        if policy == 'naive':
            idx = np.flatnonzero(~confirmed[:N] & ~locked[:N])
        else:
            alive = ~confirmed[:N]
            pp = prec0 + n_obs[:N] / sigma**2
            pm = (mu0 * prec0 + sum_obs[:N] / sigma**2) / pp
            p_skip = np.where(n_fail[:N] > 0, ndtr(-pm * np.sqrt(pp)), 0.0)
            idx = np.flatnonzero(alive & (rng.random(N) >= p_skip))
            if idx.size == 0:
                idx = np.flatnonzero(alive & (n_fail[:N] > 0))
        if idx.size == 0: break
        k = idx[rng.integers(idx.size)]
        if n_fail[k] > 0: n_retry += 1
        obs = delta[k] + rng.normal(0, sigma)
        sum_obs[k] += obs; n_obs[k] += 1; t += 1
        if obs > 0 and t < B:
            n_v = min(v_verify, B - t)
            ver = delta[k] + rng.normal(0, sigma, n_v)
            sum_obs[k] += ver.sum(); n_obs[k] += n_v; t += n_v
            if (obs + ver.sum()) / (1 + n_v) > 0:
                confirmed[k] = True
                if delta[k] > 0:
                    value += delta[k] * (B - t) / B; n_good += 1
                else:
                    value += delta[k] * min(w, B - t) / B; n_bad += 1  # self-exposing: bounded damage
                delta[N:N+C] = rng.normal(a + b * delta[k], tau_c, C); N += C
                continue
        n_fail[k] += 1
        if policy == 'naive' and rng.random() < s and not locked[k]:
            locked[k] = True
            if delta[k] > 0: n_wl += 1
    return value, n_good, n_bad, n_retry, n_wl

def sweep(B, R, sigma, mu0=-1.0, tau=1.0,
          s_grid=(0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0), reps=500, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for s in s_grid:
        vals = np.array([run_once(rng, B, R, mu0, tau, sigma, 'naive', s) for _ in range(reps)])
        rows.append(np.concatenate([[s], vals.mean(0), [vals[:,0].std()/np.sqrt(reps)]]))
    cal = np.array([run_once(rng, B, R, mu0, tau, sigma, 'calibrated') for _ in range(reps)])
    return np.array(rows), np.concatenate([cal.mean(0), [cal[:,0].std()/np.sqrt(reps)]])

if __name__ == '__main__':
    import json
    B, R = 800, 80
    results = {}
    for sigma in (0.5, 1.5, 3.0):
        rows, cal = sweep(B, R, sigma)
        results[str(sigma)] = {'rows': rows.tolist(), 'cal': cal.tolist()}
        print(f"\n=== v3  sigma={sigma} ===")
        print(" s     value(se)      good  bad  retries wl")
        for r in rows:
            print(f"{r[0]:.2f}  {r[1]:7.2f}({r[6]:.2f})  {r[2]:5.1f} {r[3]:5.1f} {r[4]:6.0f} {r[5]:5.1f}")
        print(f"CAL   {cal[0]:7.2f}({cal[5]:.2f})  {cal[1]:5.1f} {cal[2]:5.1f} {cal[3]:6.0f}")
    json.dump(results, open(_p('v3_results.json'),'w'))
