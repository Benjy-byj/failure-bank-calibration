"""End-to-end cumulative autonomous-research loop with four failure-memory policies.

Real training runs (sklearn MLP on digits). Ideas are COMPOSABLE config patches:
a confirmed idea spawns children = parent patch + one further mutation (success-gated supply).
All four policies draw from a shared run cache keyed by (config, seed), so they face the
SAME noise realizations -> paired comparison, and repeated exploration is cheap.

Policies:
  none      : no failure memory (failed ideas return to the pool)
  binary    : any failure permanently locks the idea (today's shared failure bank)
  threshold : lock only if P(dead | evidence) > theta*, else return to pool
  parole    : binary lock, but each step releases a locked idea w.p. eps

Metric: TRUE discoveries within a fixed budget of training runs = confirmed ideas whose
10-seed ground-truth mean beats the incumbent baseline.
"""
import json, os, sys, time, hashlib, warnings
warnings.filterwarnings("ignore")
import numpy as np
from scipy.stats import norm
from sklearn.datasets import load_digits
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss

X, y = load_digits(return_X_y=True)
rs = np.random.RandomState(1234); idx = rs.permutation(len(X))
tr, va = idx[:1200], idx[1200:]
sc = StandardScaler().fit(X[tr])
Xtr, Xva, ytr, yva = sc.transform(X[tr]), sc.transform(X[va]), y[tr], y[va]
LAB = np.unique(y)
if os.environ.get("NOISE", "low") == "high":      # smaller eval split -> larger measurement noise
    Xva, yva = Xva[:150], yva[:150]

NOISE = os.environ.get("NOISE", "low")     # low | high  (high: short runs + small eval split)
BUDGET = int(os.environ.get("BUDGET", 80))  # training runs per loop (the horizon knob)
_iters = 80 if NOISE == "low" else 25
BASE = dict(hidden_layer_sizes=(32,), learning_rate_init=1e-3, alpha=1e-4, batch_size=64,
            activation='relu', solver='adam', beta_1=0.9, beta_2=0.999, max_iter=_iters, tol=0.0)
POOL = {
 "lr_3e3": {"learning_rate_init": 3e-3}, "lr_1e2": {"learning_rate_init": 1e-2},
 "lr_3e4": {"learning_rate_init": 3e-4},
 "hid_64": {"hidden_layer_sizes": (64,)},
 "hid_16": {"hidden_layer_sizes": (16,)}, "hid_32_16": {"hidden_layer_sizes": (32, 16)},
 "alpha_1e5": {"alpha": 1e-5}, "alpha_1e3": {"alpha": 1e-3}, "alpha_1e2": {"alpha": 1e-2},
 "batch_32": {"batch_size": 32}, "batch_128": {"batch_size": 128},
 "tanh": {"activation": "tanh"}, "b1_085": {"beta_1": 0.85}, "b2_099": {"beta_2": 0.99},
 "iter_40": {"max_iter": _iters//2},
 "sgd_mom": {"solver": "sgd", "learning_rate_init": 1e-2, "momentum": 0.9},
 "b2_09999": {"beta_2": 0.9999},
}
TAG = os.environ.get("NOISE", "low") + "_b" + os.environ.get("BUDGET", "80")
CACHE_PATH = f"cache_{TAG}.json"
CACHE = json.load(open(CACHE_PATH)) if os.path.exists(CACHE_PATH) else {}
_dirty = [0]

def cfg_of(patch_names):
    c = dict(BASE)
    for n in patch_names:
        c.update(POOL[n])
    return c

def key(patch_names, seed):
    return hashlib.md5((",".join(sorted(patch_names)) + f"|{seed}").encode()).hexdigest()[:16]

def measure(patch_names, seed):
    """One real training run (cached across policies and replicates)."""
    k = key(patch_names, seed)
    if k in CACHE:
        return CACHE[k]
    c = cfg_of(patch_names)
    m = MLPClassifier(random_state=seed, **c)
    m.fit(Xtr, ytr)
    v = float(log_loss(yva, m.predict_proba(Xva), labels=LAB))
    CACHE[k] = v; _dirty[0] += 1
    if _dirty[0] % 50 == 0:
        json.dump(CACHE, open(CACHE_PATH, "w"))
    return v

def flush():
    json.dump(CACHE, open(CACHE_PATH, "w"))

# ---- incumbent baseline and noise scale (measured once, outside the loop budget) ----
BASE_SEEDS = list(range(300, 320))
base_runs = [measure((), s) for s in BASE_SEEDS]
BASE_MEAN, SIGMA = float(np.mean(base_runs)), float(np.std(base_runs, ddof=1))

def truth(patch_names, n=4):
    """Ground truth: mean over 10 held-out seeds; improvement = BASE_MEAN - mean."""
    runs = [measure(patch_names, 900000 + i) for i in range(n)]
    return BASE_MEAN - float(np.mean(runs))

# ---- the research loop ----
def p_dead(evidence, prior_mu, prior_tau):
    """Posterior P(effect <= 0 | evidence) under a Gaussian prior; evidence = list of improvements."""
    n = len(evidence)
    if n == 0:
        return 0.5
    ybar = float(np.mean(evidence))
    post_var = 1.0 / (1.0 / prior_tau**2 + n / SIGMA**2)
    post_mu = post_var * (prior_mu / prior_tau**2 + n * ybar / SIGMA**2)
    return float(norm.cdf(0.0, loc=post_mu, scale=np.sqrt(post_var)))

def run_loop(policy, seed, budget=None, C=3, theta=0.8, eps=0.05,
             prior_mu=-0.02, prior_tau=0.05):
    budget = budget or BUDGET
    rng = np.random.default_rng(seed)
    roots = list(POOL)
    pool = [(r,) for r in roots]                     # available ideas (tuples of patch names)
    rng.shuffle(pool)
    locked, failed_evidence, confirmed = set(), {}, []
    used = 0
    seed_ctr = seed * 10000
    while used < budget and (pool or locked):
        if not pool:                                  # nothing available
            if policy == "parole" and locked:
                rel = list(locked)[rng.integers(len(locked))]
                locked.discard(rel); pool.append(rel); continue
            break
        i = rng.integers(len(pool)); idea = pool.pop(i)
        seed_ctr += 1
        v1 = BASE_MEAN - measure(idea, seed_ctr); used += 1
        ev = [v1]
        if v1 <= 0:                                   # first-test failure
            failed_evidence[idea] = ev
            if policy == "binary" or policy == "parole":
                locked.add(idea)
            elif policy == "threshold":
                if p_dead(ev, prior_mu, prior_tau) > theta:
                    locked.add(idea)
                else:
                    pool.append(idea)                 # inconclusive -> stays available
            # policy "none": idea simply returns to the pool
            else:
                pool.append(idea)
        else:
            v2 = [BASE_MEAN - measure(idea, seed_ctr + 7000 + j) for j in range(2)]; used += 2
            ev = [v1] + v2
            if float(np.mean(ev)) > 0:                # confirmed
                confirmed.append(idea)
                kids = 0
                for m in rng.permutation(list(POOL)):
                    if m in idea: continue
                    child = tuple(sorted(idea + (m,)))
                    if child in locked or child in [c for c in pool]: continue
                    pool.append(child); kids += 1
                    if kids >= C: break
            else:                                     # verification-stage failure
                failed_evidence[idea] = ev
                if policy in ("binary", "parole"):
                    locked.add(idea)
                elif policy == "threshold":
                    if p_dead(ev, prior_mu, prior_tau) > theta:
                        locked.add(idea)
                    else:
                        pool.append(idea)
                else:
                    pool.append(idea)
        if policy == "parole" and locked and rng.random() < eps:
            rel = list(locked)[rng.integers(len(locked))]
            locked.discard(rel); pool.append(rel)
    # ---- scoring (outside budget) ----
    true_disc = [c for c in set(confirmed) if truth(c) > 0]
    best = max([truth(c) for c in set(confirmed)], default=0.0)
    return {"policy": policy, "seed": seed, "budget": budget, "used": used,
            "confirmed": len(set(confirmed)), "true_discoveries": len(true_disc),
            "best_true_gain_sigma": best / SIGMA, "locked": len(locked),
            "max_depth": max([len(c) for c in set(confirmed)], default=0)}

if __name__ == "__main__":
    wall = float(sys.argv[1]) if len(sys.argv) > 1 else 500
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    OUT = f"results_{TAG}.jsonl"
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln); done.add((r["policy"], r["seed"]))
    t0 = time.time()
    print(f"baseline {BASE_MEAN:.4f} sigma {SIGMA:.4f} (cache {len(CACHE)})")
    for rep in range(reps):
        for pol in ["none", "binary", "threshold", "parole"]:
            if (pol, 100 + rep) in done: continue
            if time.time() - t0 > wall:
                flush(); print("WALL"); sys.exit(0)
            r = run_loop(pol, 100 + rep)
            with open(OUT, "a") as f: f.write(json.dumps(r) + "\n")
            print(f"{pol:10s} rep{rep}: confirmed {r['confirmed']:2d} true {r['true_discoveries']:2d} "
                  f"best {r['best_true_gain_sigma']:.2f}s depth {r['max_depth']} locked {r['locked']} ({time.time()-t0:.0f}s)")
    flush(); print("COMPLETE")
