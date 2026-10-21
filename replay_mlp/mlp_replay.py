"""Domain 2: verdict-pipeline replay on a tabular-classification HPO loop (sklearn MLP on digits).
Different task family, model class, and noise source (weight init + adam stochasticity) from the GPT loop.
Resumable via log.jsonl. Phases: baseline(20) -> verdict(1/mutation) -> verify(2 for passers) -> truth(10/mutation).
"""
import json, os, sys, time, warnings
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
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

BASE = dict(hidden_layer_sizes=(32,), learning_rate_init=1e-3, alpha=1e-4, batch_size=64,
            activation='relu', solver='adam', beta_1=0.9, beta_2=0.999, max_iter=80, tol=0.0)
MUT = {
 "lr_3e4":{"learning_rate_init":3e-4}, "lr_3e3":{"learning_rate_init":3e-3}, "lr_1e2":{"learning_rate_init":1e-2},
 "lr_1e4":{"learning_rate_init":1e-4},
 "hid_16":{"hidden_layer_sizes":(16,)}, "hid_64":{"hidden_layer_sizes":(64,)}, "hid_32_16":{"hidden_layer_sizes":(32,16)},
 "hid_8":{"hidden_layer_sizes":(8,)}, "hid_128":{"hidden_layer_sizes":(128,)},
 "alpha_1e5":{"alpha":1e-5}, "alpha_1e3":{"alpha":1e-3}, "alpha_1e2":{"alpha":1e-2}, "alpha_1e1":{"alpha":1e-1},
 "batch_32":{"batch_size":32}, "batch_128":{"batch_size":128}, "batch_256":{"batch_size":256},
 "act_tanh":{"activation":"tanh"}, "act_logistic":{"activation":"logistic"},
 "b1_085":{"beta_1":0.85}, "b1_095":{"beta_1":0.95}, "b2_099":{"beta_2":0.99}, "b2_09999":{"beta_2":0.9999},
 "iter_40":{"max_iter":40}, "iter_160":{"max_iter":160}, "iter_240":{"max_iter":240},
 "sgd_mom":{"solver":"sgd","learning_rate_init":1e-2,"momentum":0.9,"nesterovs_momentum":True},
 "sgd_adaptive":{"solver":"sgd","learning_rate":"adaptive","learning_rate_init":1e-2,"momentum":0.9},
 "early_stop":{"early_stopping":True,"validation_fraction":0.15,"n_iter_no_change":10},
}
LOG = _p("log.jsonl")
done = {}
if os.path.exists(LOG):
    for ln in open(LOG):
        r = json.loads(ln); done[(r["phase"], r["name"], r["seed"])] = r["loss"]

def run_cfg(seed, patch):
    c = dict(BASE); c.update(patch)
    m = MLPClassifier(random_state=seed, **c)
    m.fit(Xtr, ytr)
    return float(log_loss(yva, m.predict_proba(Xva), labels=np.unique(y)))

def do(phase, name, seed, patch):
    k = (phase, name, seed)
    if k in done: return done[k]
    v = run_cfg(seed, patch)
    with open(LOG, "a") as f:
        f.write(json.dumps({"phase": phase, "name": name, "seed": seed, "loss": v}) + "\n")
    done[k] = v
    return v

budget_s = float(sys.argv[1]) if len(sys.argv) > 1 else 400
t0 = time.time()
def timeleft(): return time.time() - t0 < budget_s

for s in range(20):
    if not timeleft(): print("budget out (baseline)"); sys.exit(0)
    do("baseline", "base", s, {})
base = [done[("baseline","base",s)] for s in range(20)]
bm = float(np.mean(base))
for i, name in enumerate(MUT):
    if not timeleft(): print("budget out (verdict)"); sys.exit(0)
    v = do("verdict", name, 1000+i, MUT[name])
    if v < bm:
        for j in range(2):
            if not timeleft(): print("budget out (verify)"); sys.exit(0)
            do("verify", name, 1500+10*i+j, MUT[name])
for i, name in enumerate(MUT):
    for j in range(10):
        if not timeleft(): print("budget out (truth)"); sys.exit(0)
        do("truth", name, 2000+100*i+j, MUT[name])
print(f"COMPLETE: {len(done)} runs, {time.time()-t0:.0f}s")
