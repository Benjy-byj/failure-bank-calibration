"""Stage 2: enrich the config population around measured near-null effects to
populate the verification stage, then compare measured W_B against the theory
prediction computed from THIS population's measured effect distribution and sigma.
Seeds remain globally unique (new blocks). Resumable. Usage: python wb_rep2.py <seconds>
"""
import json, os, sys, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.datasets import load_digits
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss
from scipy import stats

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
P = list(GRID); ITER = 40
T0 = time.time(); SEC = float(sys.argv[1]) if len(sys.argv) > 1 else 200
cache = {}
CF = "wb/cache.jsonl"
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

S1 = json.load(open("wb/wb_results.json"))
BM, SIG = S1["BM"], S1["SIG"]
# marginal anchors: stage-1 verify-reaching configs with |true effect| < 0.7 sigma
anchors = [tuple(e["cfg"]) for e in S1["events"]
           if e["stage"] == "verify" and abs(BM - e["true"]) < 0.7 * SIG]
stage1_cfgs = {tuple(e["cfg"]) for e in S1["events"]}
rng = np.random.default_rng(777)
new = set()
tries = 0
while len(new) < 620 and tries < 400_000:
    tries += 1
    a = anchors[rng.integers(len(anchors))]
    c = list(a)
    for _ in range(int(rng.integers(1, 3))):
        i = int(rng.integers(len(P)))
        c[i] = int(np.clip(c[i] + rng.choice([-1, 1]), 0, len(GRID[P[i]]) - 1))
    t = tuple(c)
    if t not in stage1_cfgs: new.add(t)
new = sorted(new)
print(f"marginal anchors {len(anchors)}; stage-2 configs {len(new)}")

events = []
STATE = "wb/wb2_events.json"
done = json.load(open(STATE)) if os.path.exists(STATE) else []
events = done
start = len(done)
for ei in range(start, len(new)):
    cfg = new[ei]
    s0 = 400_000 + 20 * ei
    l1 = train(cfg, s0)
    if l1 >= BM:
        e = dict(cfg=list(cfg), stage="first", conv=True)
    else:
        v1, v2 = train(cfg, s0 + 1), train(cfg, s0 + 2)
        e = dict(cfg=list(cfg), stage="verify", conv=bool((l1 + v1 + v2) / 3 >= BM))
    events.append(e)
    if ei % 25 == 0: json.dump(events, open(STATE, "w"))
json.dump(events, open(STATE, "w"))

need = [e for e in events if e["stage"] == "verify" and e.get("true") is None]
for ei, e in enumerate([e for e in events if e["stage"] == "verify"]):
    if e.get("true") is not None: continue
    s0 = 700_000 + 10 * ei
    e["true"] = float(np.mean([train(tuple(e["cfg"]), s0 + j) for j in range(8)]))
    json.dump(events, open(STATE, "w"))
json.dump(events, open(STATE, "w"))

# pooled analysis over stage 1 + stage 2 (independent events throughout)
all_ev = [e for e in S1["events"]] + events
vb = [e for e in all_ev if e["stage"] == "verify" and e["conv"]]
wrong = [e for e in vb if BM - e["true"] > 0]
n, k = len(vb), len(wrong)
lo = stats.beta.ppf(0.025, k, n - k + 1) if k else 0.0
hi = stats.beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
print(f"POOLED: verification-stage convictions n={n}, wrongful k={k}: W_B={k/n:.3f} [95% CI {lo:.3f},{hi:.3f}]")

# matched theory prediction: empirical-prior MC using this pooled population's measured
# effects (verify-reaching configs' truths) and measured sigma
truths = np.array([BM - e["true"] for e in all_ev if e["stage"] == "verify"])
mc = np.random.default_rng(1)
Wb_mc_num = Wb_mc_den = 0
for _ in range(200_000):
    d = truths[mc.integers(len(truths))]
    l1 = -d + mc.normal(0, SIG)           # observed first-run delta (loss scale, sign: worse=+)
    if l1 >= 0: continue                   # first-test conviction, not verification-stage
    m3 = (l1 + (-d + mc.normal(0, SIG)) + (-d + mc.normal(0, SIG))) / 3
    if m3 >= 0:
        Wb_mc_den += 1
        if d > 0: Wb_mc_num += 1
print(f"matched theory W_B (empirical-prior MC, same population, measured sigma): {Wb_mc_num/max(1,Wb_mc_den):.3f}")
eff_w = sorted(round((BM - e['true'])/SIG, 2) for e in wrong)
print(f"wrongful true effects (sigma): {eff_w[:20]}{'...' if len(eff_w)>20 else ''}")
conf = [e for e in all_ev if e["stage"] == "verify" and not e["conv"]]
fc = sum(1 for e in conf if BM - e["true"] <= 0)
print(f"confirmed {len(conf)}, false confirms {fc} ({fc/max(1,len(conf)):.3f})")
json.dump(dict(n=n, k=k, ci=[lo, hi], theory=Wb_mc_num/max(1,Wb_mc_den)), open("wb/wb2_summary.json", "w"))
