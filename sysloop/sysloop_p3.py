"""P3 extension: rate-matched parole (PREREG_P3.md). Replays graded for r*, runs parole_matched, preserves prior truth."""
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
MATCH_NS = 700_000  # fresh seed namespace for parole_matched

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


import math
OLD = json.load(open("results/sysloop.json"))
BM, SIG = OLD["BM"], OLD["SIG"]  # reuse recorded baseline exactly

def run_loop(cond, rep, reopen_rate=None, count_only=False):
    rng = np.random.default_rng(int(hashlib.md5(f"{cond}-{rep}".encode()).hexdigest()[:8], 16))
    seed_ctr = [0]
    def next_seed():
        seed_ctr[0] += 1
        ns = MATCH_NS if cond == "parole_matched" else 100_000 * (CONDS.index(cond) + 1)
        return ns + 10_000 * rep + seed_ctr[0]
    confirmed, locked, evidence = [], set(), {}
    budget = BUDGET
    enc = reop = 0
    while budget > 0:
        for _ in range(60):
            parent = BASE_CFG if not confirmed else confirmed[rng.integers(len(confirmed))]
            p = rng.integers(len(PARAMS))
            step = rng.choice([-1, 1])
            j = int(np.clip(parent[p] + step, 0, len(GRID[PARAMS[p]]) - 1))
            cfg = tuple(j if k == p else parent[k] for k in range(len(PARAMS)))
            if cfg == parent:
                continue
            if cond == "parole_matched" and cfg in locked:
                if rng.random() < reopen_rate:
                    locked.discard(cfg); break
                continue
            if cond == "graded" and cfg in evidence:
                enc += 1
                obs = evidence[cfg]
                z = (np.mean(obs) - BM) / (SIG / np.sqrt(len(obs)))
                if 1 - 0.5 * (1 + math.erf(-z / np.sqrt(2))) < 0.2:
                    continue
                reop += 1
            break
        else:
            break
        l1, _ = train(cfg, next_seed()); budget -= 1
        if cond == "graded":
            evidence.setdefault(cfg, []).append(l1)
        if l1 >= BM:
            if cond in ("parole_matched",):
                locked.add(cfg)
            continue
        if budget < 2:
            break
        v1, _ = train(cfg, next_seed()); v2, _ = train(cfg, next_seed()); budget -= 2
        if cond == "graded":
            evidence[cfg] += [v1, v2]
        if (l1 + v1 + v2) / 3 < BM:
            if cfg not in confirmed:
                confirmed.append(cfg)
        else:
            if cond in ("parole_matched",):
                locked.add(cfg)
    return dict(confirmed=[list(c) for c in confirmed], n_locked=len(locked), enc=enc, reop=reop)

# 1) replay graded for r* (cache makes this free; verify replay matches recorded confirmed sets)
ENC = REOP = 0
for rep in range(REPS):
    s = run_loop("graded", rep)
    rec = OLD["state"][f"graded-{rep}"]["confirmed"]
    assert s["confirmed"] == rec, f"replay mismatch rep {rep}"
    ENC += s["enc"]; REOP += s["reop"]
rstar = REOP / ENC
print(f"graded replay verified identical; encounters={ENC}, reopens={REOP}, r* = {rstar:.3f}")

# 2) parole_matched
state = {}
for rep in range(REPS):
    state[f"parole_matched-{rep}"] = run_loop("parole_matched", rep, reopen_rate=rstar)
    print(f"[parole_matched rep{rep}] confirmed={len(state[f'parole_matched-{rep}']['confirmed'])}")

# 3) truth: PRESERVE old values, test only new configs in a fresh seed namespace
truth = dict(OLD["truth"])
newcfg = sorted({tuple(c) for s in state.values() for c in s["confirmed"]} - {tuple(json.loads(k)) for k in OLD["truth"]})
for i, cfg in enumerate(newcfg):
    truth[str(list(cfg))] = float(np.mean([train(cfg, 950_000 + 100 * i + j)[0] for j in range(6)]))
print(f"{len(newcfg)} new configs truth-tested; {len(OLD['truth'])} preserved")
json.dump(dict(rstar=rstar, enc=ENC, reop=REOP, state=state, truth=truth), open("results/sysloop_p3.json", "w"), indent=1)

# 4) analysis
from itertools import combinations
def disc(st_all, tr, key):
    return [sum((BM - tr[str(c)]) / SIG > 0 for c in st_all[f"{key}-{r}"]["confirmed"]) for r in range(REPS)]
d_m = disc(state, truth, "parole_matched")
d_g = disc(OLD["state"], truth, "graded")
d_p = disc(OLD["state"], truth, "parole")
def mwp(a, b):
    U = sum(x > y for x in a for y in b); pool = a + b; ge = tot = 0
    for idx in combinations(range(16), 8):
        aa = [pool[i] for i in idx]; bb = [pool[i] for i in range(16) if i not in idx]
        tot += 1; ge += (sum(x > y for x in aa for y in bb) >= U)
    return ge / tot
print(f"parole_matched: {d_m} (mean {np.mean(d_m):.1f}±{np.std(d_m, ddof=1):.1f})")
print(f"graded>matched one-sided exact p = {mwp(d_g, d_m):.4f}  | matched>plain-parole p = {mwp(d_m, d_p):.4f}")
print(f"(recorded: graded {np.mean(d_g):.1f}, plain parole {np.mean(d_p):.1f})")
