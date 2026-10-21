import json, numpy as np
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
S = json.load(open(_p('summary.json')))
bm, bs, nb = S['baseline']['mean'], S['baseline']['std'], S['baseline']['n']
names = list(S['verdicts'])
E = np.array([bm - S['truth'][k]['mean'] for k in names])
se = np.array([np.sqrt(S['truth'][k]['std']**2/S['truth'][k]['n'] + bs**2/nb) for k in names])
sig = bs
rng = np.random.default_rng(0); M = 200000
# leave-one-out: predict W_A contribution of idea i using prior built from the other 35
def p_wrong_given_fail(prior_effects, prior_se):
    e = rng.choice(prior_effects, M) + rng.normal(0, prior_se, M)
    obs = e + rng.normal(0, sig, M)
    sel = obs <= 0
    return e, obs, sel
# LOO W_A: for each i, P(fail | e_i-ish) weighting... simplest faithful LOO version:
# simulate the full pipeline where the tested idea's true effect ~ its OWN measured (e_i, se_i),
# and the CLASSIFIER (P(good|fail)) is irrelevant -- what we predict is the aggregate rate:
# W_A_loo = sum_i P(e_i'>0, obs_i<=0) / sum_i P(obs_i<=0), with e_i' ~ N(e_i, se_i) but
# to be honest-LOO we must NOT use e_i for idea i's own prior... The rate prediction for the
# POOL uses each idea's truth only for itself (that's measurement, not prior). The circular
# part in the original was using all 36 to form the prior INCLUDING idea i when predicting i.
# Faithful LOO: predict P(wrong|fail) for idea i via prior from others, then aggregate by
# each idea's fail probability under that prior... but idea i's identity is unknown pre-hoc.
# Cleanest LOO aggregate: for each i, draw e from prior_{-i}, compute joint; average over i.
num = den = 0.0
for i in range(len(names)):
    mask = np.ones(len(names), bool); mask[i] = False
    e = rng.choice(E[mask], M//36 + 1) + rng.normal(0, se[mask].mean(), M//36 + 1)
    obs = e + rng.normal(0, sig, M//36 + 1)
    sel = obs <= 0
    num += (e[sel] > 0).sum(); den += sel.sum()
print(f"W_A leave-one-out prediction: {num/den:.3f}  (full-sample version was 0.19; measured 0.175 [CI 0.117,0.253])")
# same for W_B
num = den = 0.0
for i in range(len(names)):
    mask = np.ones(len(names), bool); mask[i] = False
    n = M//36 + 1
    e = rng.choice(E[mask], n) + rng.normal(0, se[mask].mean(), n)
    x1 = e + rng.normal(0, sig, n)
    s3 = x1 + rng.normal(0, sig, n) + rng.normal(0, sig, n)
    sel = (x1 > 0) & (s3 <= 0)
    num += (e[sel] > 0).sum(); den += sel.sum()
print(f"W_B leave-one-out prediction: {num/den:.3f}  (full-sample 0.34; measured 0.50 [0.28,0.72])")
