"""W_B replication with fully independent seeds (kills the correlated-events caveat).
Design: ~450 distinct configs from the 1-2-step neighborhood of baseline (marginal-rich
by construction), each gets ONE verdict event with globally unique seeds:
first test (1 seed) -> if better than baseline mean, 2 verification seeds -> conviction
if 3-run mean >= baseline mean. Ground truth = 8 more unique seeds per convicted/passed
config. W_B = P(true effect > 0 | verification-stage conviction), exact binomial CI.
Also yields W_A on the same set. Resumable via run cache.
Usage: python wb_rep.py <seconds>
"""
import json, os, sys, time, itertools, warnings
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.datasets import load_digits
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss

X, y = load_digits(return_X_y=True)
rs = np.random.RandomState(1234); idx = rs.permutation(len(X))
tr, va = idx[:1200], idx[1200:]
sc = StandardScaler().fit(X[tr])
Xtr, Xva, ytr, yva = sc.transform(X[tr]), sc.transform(X[va]), y[tr], y[va]

GRID = {"lr": [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2],
        "hidden": [(8,), (16,), (32,), (64,), (128,), (32, 16)],
        "alpha": [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1],
        "batch": [32, 64, 128, 256],
        "act": ["relu", "tanh", "logistic"],
        "b1": [0.85, 0.9, 0.95]}
P = list(GRID); BASE = (2, 2, 2, 1, 0, 1); ITER = 40
T0 = time.time(); SEC = float(sys.argv[1]) if len(sys.argv) > 1 else 200
os.makedirs("wb", exist_ok=True)
cache = {}
CF = "wb/cache.jsonl"
if os.path.exists(CF):
    for ln in open(CF):
        r = json.loads(ln); cache[(tuple(r["c"]), r["s"])] = r["l"]

def train(cfg, seed):
    k = (cfg, seed)
    if k in cache: return cache[k]
    if time.time() - T0 > SEC:
        print(f"TIME OUT ({len(cache)} cached)"); sys.exit(0)
    c = {p: GRID[p][cfg[i]] for i, p in enumerate(P)}
    m = MLPClassifier(hidden_layer_sizes=c["hidden"], learning_rate_init=c["lr"],
                      alpha=c["alpha"], batch_size=c["batch"], activation=c["act"],
                      beta_1=c["b1"], solver="adam", max_iter=ITER, tol=0.0, random_state=seed)
    m.fit(Xtr, ytr)
    l = float(log_loss(yva, m.predict_proba(Xva), labels=np.unique(y)))
    cache[k] = l
    with open(CF, "a") as f: f.write(json.dumps({"c": list(cfg), "s": seed, "l": l}) + "\n")
    return l

# baseline: 24 dedicated seeds (mirrors the charGPT protocol's 24-seed baseline)
base = [train(BASE, 1_000 + i) for i in range(24)]
BM, SIG = float(np.mean(base)), float(np.std(base, ddof=1))

# config set: all 1-step neighbors + sampled 2-step neighbors, deduplicated
rng = np.random.default_rng(20260821)
cfgs = set()
for i, p in enumerate(P):
    for d in (-1, 1):
        j = BASE[i] + d
        if 0 <= j < len(GRID[p]):
            cfgs.add(tuple(j if k == i else BASE[k] for k in range(len(P))))
one_step = sorted(cfgs)
tries = 0
while len(cfgs) < 450 and tries < 200_000:
    tries += 1
    m = int(rng.integers(1, 4))                       # perturb 1-3 params
    which = rng.choice(len(P), m, replace=False)
    c = list(BASE)
    for a in which:
        c[a] = int(np.clip(c[a] + rng.choice([-2, -1, 1, 2]), 0, len(GRID[P[a]]) - 1))
    if tuple(c) != BASE:
        cfgs.add(tuple(c))
cfgs = sorted(cfgs)

# one fully-independent verdict event per config; globally unique seeds
events = []
for ei, cfg in enumerate(cfgs):
    s0 = 10_000 + 20 * ei          # block of 20 seeds reserved per event
    l1 = train(cfg, s0)
    if l1 >= BM:
        events.append(dict(cfg=cfg, stage="first", conv=True)); continue
    v1, v2 = train(cfg, s0 + 1), train(cfg, s0 + 2)
    m3 = (l1 + v1 + v2) / 3
    events.append(dict(cfg=cfg, stage="verify", conv=bool(m3 >= BM)))

# truth for every config that reached verification (both convicted and confirmed)
need_truth = [e for e in events if e["stage"] == "verify"]
for ei, e in enumerate(need_truth):
    s0 = 200_000 + 10 * ei
    e["true"] = float(np.mean([train(e["cfg"], s0 + j) for j in range(8)]))

out = dict(BM=BM, SIG=SIG, n_cfg=len(cfgs), events=[
    dict(cfg=list(e["cfg"]), stage=e["stage"], conv=e["conv"], true=e.get("true")) for e in events])
json.dump(out, open("wb/wb_results.json", "w"))

from scipy import stats
vb = [e for e in events if e["stage"] == "verify" and e["conv"]]
wrong = [e for e in vb if BM - e["true"] > 0]
n, k = len(vb), len(wrong)
lo, hi = stats.beta.ppf(0.025, k, n - k + 1) if k else 0.0, stats.beta.ppf(0.975, k + 1, n - k)
first_conv = [e for e in events if e["stage"] == "first" and e["conv"]]
confirmed = [e for e in events if e["stage"] == "verify" and not e["conv"]]
false_conf = [e for e in confirmed if BM - e["true"] <= 0]
print(f"baseline {BM:.4f}±{SIG:.4f}; configs {len(cfgs)}; first-test convictions {len(first_conv)}")
print(f"verification-stage convictions n={n}, wrongful k={k}: W_B = {k/n:.3f}  [95% CI {lo:.3f},{hi:.3f}]  (all seeds independent)")
print(f"confirmed {len(confirmed)}, false confirms {len(false_conf)} ({len(false_conf)/max(1,len(confirmed)):.2f})")
effs = sorted(round((BM - e['true'])/SIG, 2) for e in wrong)
print(f"wrongful-conviction true effects (sigma): {effs}")
