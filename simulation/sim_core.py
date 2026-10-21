import numpy as np
from scipy.special import ndtr

def run_once(rng, B, R, mu0, tau, sigma, policy, s=None,
             v_verify=2, C=3, b=0.6, mu_c0=-0.27, anchor=0.55, tau_c=0.8, w=80):
    cap = B * (1 + C) + R + 8
    delta = np.empty(cap); n_fail = np.zeros(cap, np.int32)
    locked = np.zeros(cap, bool); confirmed = np.zeros(cap, bool)
    sum_obs = np.zeros(cap); n_obs = np.zeros(cap, np.int32)
    delta[:R] = rng.normal(mu0, tau, R); N = R
    prec0 = 1.0 / tau**2
    value = 0.0; n_good = 0; n_bad = 0; n_retry = 0; n_wl = 0; n_lock = 0
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
                    value += delta[k] * min(w, B - t) / B; n_bad += 1
                delta[N:N+C] = rng.normal(mu_c0 + b * (delta[k] - anchor), tau_c, C); N += C
                continue
        n_fail[k] += 1
        if policy == 'naive' and rng.random() < s and not locked[k]:
            locked[k] = True; n_lock += 1
            if delta[k] > 0: n_wl += 1
    return value, n_good, n_bad, n_retry, n_wl, n_lock

def sweep_s(B, R, sigma, s_grid, reps, seed=0, **kw):
    rng = np.random.default_rng(seed)
    rows = []
    for s in s_grid:
        vals = np.array([run_once(rng, B, R, -1.0, 1.0, sigma, 'naive', s, **kw) for _ in range(reps)])
        rows.append(np.concatenate([[s], vals.mean(0),
                                    [vals[:,1].std()/np.sqrt(reps)]]))  # SE of good count
    cal = np.array([run_once(rng, B, R, -1.0, 1.0, sigma, 'calibrated', **kw) for _ in range(reps)])
    return np.array(rows), np.concatenate([cal.mean(0), [cal[:,1].std()/np.sqrt(reps)]])
