"""End-to-end system experiment: four memory conditions, real training runs, fixed budget.
Conditions: nomem / binary / graded (theta*=0.8, evidence pooling) / parole (5%).
Cumulative supply: proposals are grid-neighbors of confirmed configs (success-gated).
Resumable: all runs cached by (config, seed); loops are deterministic per (cond, rep).
Usage: python sysloop.py <seconds_budget>
"""
import json, os, sys, time, hashlib, warnings
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

GRID = {
    "lr":     [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2],
    "hidden": [(8,), (16,), (32,), (64,), (128,), (32, 16)],
    "alpha":  [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1],
    "batch":  [32, 64, 128, 256],
    "act":    ["relu", "tanh", "logistic"],
    "b1":     [0.85, 0.9, 0.95],
}
PARAMS = list(GRID)
BASE_CFG = (2, 2, 2, 1, 0, 1)  # lr=1e-3, hidden=(32,), alpha=1e-4, batch=64, relu, b1=0.9
ITER = 40
BUDGET = 220
REPS = 8
CONDS = ["nomem", "binary", "graded", "parole", "lcb"]

os.makedirs("results", exist_ok=True)
CACHE_F = "results/cache.jsonl"
cache = {}
if os.path.exists(CACHE_F):
    for ln in open(CACHE_F):
        r = json.loads(ln)
        cache[(tuple(r["cfg"]), r["seed"])] = r["loss"]

T0 = time.time()
SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 480

def train(cfg, seed):
    key = (cfg, seed)
    if key in cache:
        return cache[key], True
    if time.time() - T0 > SECONDS:
        print(f"TIME BUDGET OUT ({len(cache)} cached runs)"); sys.exit(0)
    c = {p: GRID[p][cfg[i]] for i, p in enumerate(PARAMS)}
    m = MLPClassifier(hidden_layer_sizes=c["hidden"], learning_rate_init=c["lr"],
                      alpha=c["alpha"], batch_size=c["batch"], activation=c["act"],
                      beta_1=c["b1"], solver="adam", max_iter=ITER, tol=0.0,
                      random_state=seed)
    m.fit(Xtr, ytr)
    loss = float(log_loss(yva, m.predict_proba(Xva), labels=np.unique(y)))
    cache[(cfg, seed)] = loss
    with open(CACHE_F, "a") as f:
        f.write(json.dumps({"cfg": list(cfg), "seed": seed, "loss": loss}) + "\n")
    return loss, False

# shared baseline
base_runs = [train(BASE_CFG, 10_000 + i)[0] for i in range(12)]
BM, SIG = float(np.mean(base_runs)), float(np.std(base_runs, ddof=1))

def run_loop(cond, rep):
    rng = np.random.default_rng(int(hashlib.md5(f"{cond}-{rep}".encode()).hexdigest()[:8], 16))
    seed_ctr = [0]
    def next_seed():
        seed_ctr[0] += 1
        return 100_000 * (CONDS.index(cond) + 1) + 10_000 * rep + seed_ctr[0]
    confirmed, locked, evidence = [], set(), {}
    budget = BUDGET
    tested_events = 0
    while budget > 0:
        # propose: neighbor of a confirmed config (success-gated) or baseline
        for _ in range(60):
            parent = BASE_CFG if not confirmed else confirmed[rng.integers(len(confirmed))]
            p = rng.integers(len(PARAMS))
            step = rng.choice([-1, 1])
            j = int(np.clip(parent[p] + step, 0, len(GRID[PARAMS[p]]) - 1))
            cfg = tuple(j if k == p else parent[k] for k in range(len(PARAMS)))
            if cfg == parent:
                continue
            if cond == "binary" and cfg in locked:
                continue
            if cond == "parole" and cfg in locked:
                if rng.random() < 0.05:
                    locked.discard(cfg); break
                continue
            if cond == "graded" and cfg in evidence:
                obs = evidence[cfg]
                z = (np.mean(obs) - BM) / (SIG / np.sqrt(len(obs)))
                if 1 - 0.5 * (1 + __import__("math").erf(-z / np.sqrt(2))) < 0.2:  # P(dead)>0.8
                    continue
            if cond == "lcb" and cfg in evidence:
                obs = evidence[cfg]
                # successive-elimination: eliminate only if the config's lower confidence bound
                # on improvement is still negative, i.e. mean loss - beta*SE > baseline mean
                if np.mean(obs) - 1.0 * (SIG / np.sqrt(len(obs))) > BM:
                    continue
            break
        else:
            break  # proposal space exhausted
        # first test
        l1, _ = train(cfg, next_seed()); budget -= 1; tested_events += 1
        if cond in ("graded", "lcb"):
            evidence.setdefault(cfg, []).append(l1)
        if l1 >= BM:
            if cond in ("binary", "parole"):
                locked.add(cfg)
            continue
        # verification
        if budget < 2:
            break
        v1, _ = train(cfg, next_seed()); v2, _ = train(cfg, next_seed()); budget -= 2
        if cond in ("graded", "lcb"):
            evidence[cfg] += [v1, v2]
        if (l1 + v1 + v2) / 3 < BM:
            if cfg not in confirmed:
                confirmed.append(cfg)
        else:
            if cond in ("binary", "parole"):
                locked.add(cfg)
    return dict(confirmed=[list(c) for c in confirmed], n_locked=len(locked),
                tested=tested_events)

state = {}
for cond in CONDS:
    for rep in range(REPS):
        state[f"{cond}-{rep}"] = run_loop(cond, rep)
        print(f"[{cond} rep{rep}] confirmed={len(state[f'{cond}-{rep}']['confirmed'])} "
              f"locked={state[f'{cond}-{rep}']['n_locked']} tested={state[f'{cond}-{rep}']['tested']}")

# post-hoc ground truth on every distinct confirmed config (6 seeds, offline)
distinct = sorted({tuple(c) for s in state.values() for c in s["confirmed"]})
truth = {}
for cfg in distinct:
    runs = [train(cfg, 900_000 + 100 * distinct.index(cfg) + j)[0] for j in range(6)]
    truth[str(list(cfg))] = float(np.mean(runs))
out = dict(BM=BM, SIG=SIG, base_runs=base_runs, budget=BUDGET, iters=ITER,
           state=state, truth=truth)
with open("results/sysloop.json", "w") as f:
    json.dump(out, f, indent=1)
print(f"DONE: baseline {BM:.4f}±{SIG:.4f}; {len(distinct)} distinct confirmed configs truth-tested; total cached runs {len(cache)}")
