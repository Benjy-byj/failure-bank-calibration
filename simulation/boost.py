import json, numpy as np
from scipy.special import ndtr

import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
S = json.load(open(_p('summary.json', 'replay_chargpt')))
bm, bs, nb = S['baseline']['mean'], S['baseline']['std'], S['baseline']['n']
eff, se_eff = {}, {}
for k in S['truth']:
    t = S['truth'][k]
    eff[k] = bm - t['mean']; se_eff[k] = np.sqrt(t['std']**2/t['n'] + bs**2/nb)

vals = {}
order = {}
for ln in open(_p('ext_log.txt', 'replay_chargpt')):
    ph, name, seed, v = ln.split()
    vals[(name, int(seed))] = float(v)
    order.setdefault(name, []).append((ph, int(seed), float(v)))

names = sorted(set(n for n, s in vals if True))
# replay orchestrator logic
MUT_ORDER = ["lr_2e3","lr_4e3","lr_1.5e3","lr_6e3","lr_1e3","warmup_50","warmup_300","warmup_0",
 "wd_0.05","wd_0.2","wd_0","dropout_0.05","dropout_0.1","dropout_0.2","attn_dropout_0.05",
 "beta2_0.95","beta2_0.999","beta1_0.85","clip_0.5","clip_2","clip_off","init_0.01","init_0.03",
 "init_0.005","sched_linear","sched_wsd","sched_const","lrmin_0.0","lrmin_0.3","label_smooth_0.05",
 "label_smooth_0.1","untie","no_bias","relu","embd_lr_2x","embd_lr_0.5x"]
n_verdict = sum(1 for ln in open(_p('ext_log.txt', 'replay_chargpt')) if ln.startswith('verdict_r'))
assert n_verdict == 180, n_verdict
events = []   # (name, kind) kind: 'convictA' (single-shot fail), 'convictB' (verify fail), 'confirm'
shared_flags = []
for i, name in enumerate(MUT_ORDER):
    for r in range(5):
        s = 3000 + 100*i + r
        v = vals[(name, s)]
        if v >= bm:
            events.append((name, 'convictA')); continue
        v1, v2s = s+50, s+51
        # replay caching: a verify seed value comes from ext_log if present, else it was cached — find it among earlier verify seeds of same mutation
        def getv(seed):
            if (name, seed) in vals: return vals[(name, seed)], False
            return None, True
        a, m1 = getv(v1); b, m2 = getv(v2s)
        # cached seeds must exist in vals under same (name,seed) from an earlier verdict's verify — they do by construction
        if a is None: a = vals[(name, v1)] if (name, v1) in vals else None
        if b is None: b = vals[(name, v2s)] if (name, v2s) in vals else None
        # if truly absent (never run because cached from *earlier verdict* whose verify seed equals this one), it must be in vals already; assert
        assert a is not None and b is not None, (name, s, v1, v2s)
        mean3 = (v + a + b) / 3
        events.append((name, 'confirm' if mean3 < bm else 'convictB'))

# pool with original round (from summary)
for k in S['verdicts']:
    vd = S['verdicts'][k]
    if not vd['pass']: events.append((k, 'convictA'))
    elif vd.get('confirmed') is False: events.append((k, 'convictB'))
    else: events.append((k, 'confirm'))

def wilson(k, n):
    if n == 0: return (float('nan'),)*3
    p = k/n; z = 1.96
    den = 1 + z*z/n; c = (p + z*z/(2*n))/den; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return p, c-h, c+h

for kind, label in [('convictA','single-shot convictions (W_A)'), ('convictB','verification convictions (W_B)')]:
    ev = [e for e in events if e[1] == kind]
    wrong = [e for e in ev if eff[e[0]] > 0]
    exp = sum(ndtr(eff[e[0]]/se_eff[e[0]]) for e in ev)
    p, lo, hi = wilson(len(wrong), len(ev))
    print(f"{label}: n={len(ev)}, wrongful={len(wrong)} -> {p:.3f} [95% CI {lo:.3f},{hi:.3f}] | measurement-aware {exp/len(ev):.3f}")
    from collections import Counter
    print("   wrongful by mutation:", dict(Counter(e[0] for e in wrong)))
conf = [e for e in events if e[1]=='confirm']
fc = [e for e in conf if eff[e[0]] <= 0]
print(f"confirmations: n={len(conf)}, false confirms={len(fc)} ({[e[0] for e in fc]})")
print(f"theory (empirical-prior MC, prior round): W_A 0.19, W_B 0.34")
