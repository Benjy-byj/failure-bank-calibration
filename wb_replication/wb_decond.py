import json, time, sys, warnings
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
GRID = {"lr": [1e-4,3e-4,1e-3,3e-3,1e-2,3e-2], "hidden": [(8,),(16,),(32,),(64,),(128,),(32,16)],
        "alpha": [1e-6,1e-5,1e-4,1e-3,1e-2,1e-1], "batch": [32,64,128,256],
        "act": ["relu","tanh","logistic"], "b1": [0.85,0.9,0.95]}
P = list(GRID); ITER = 40
T0 = time.time(); SEC = float(sys.argv[1]) if len(sys.argv)>1 else 185
cache = {}
for ln in open("wb/cache.jsonl"):
    r = json.loads(ln); cache[(tuple(r["c"]), r["s"])] = r["l"]
def train(cfg, seed):
    k = (cfg, seed)
    if k in cache: return cache[k]
    if time.time()-T0 > SEC: print(f"TIME OUT ({len(cache)})"); sys.exit(0)
    c = {p: GRID[p][cfg[i]] for i,p in enumerate(P)}
    m = MLPClassifier(hidden_layer_sizes=c["hidden"], learning_rate_init=c["lr"], alpha=c["alpha"],
                      batch_size=c["batch"], activation=c["act"], beta_1=c["b1"],
                      solver="adam", max_iter=ITER, tol=0.0, random_state=seed)
    m.fit(Xtr, ytr)
    l = float(log_loss(yva, m.predict_proba(Xva), labels=np.unique(y)))
    cache[k] = l
    with open("wb/cache.jsonl","a") as f: f.write(json.dumps({"c": list(cfg), "s": seed, "l": l})+"\n")
    return l
S1 = json.load(open("wb/wb_results.json")); BM, SIG = S1["BM"], S1["SIG"]
ev2 = json.load(open("wb/wb2_events.json"))
all_ev = S1["events"] + ev2
firsts = [tuple(e["cfg"]) for e in all_ev if e["stage"]=="first"]
rng = np.random.default_rng(5)
samp = [firsts[i] for i in rng.choice(len(firsts), 60, replace=False)]
truth_f = {}
for ei, cfg in enumerate(samp):
    s0 = 900_000 + 10*ei
    truth_f[str(list(cfg))] = float(np.mean([train(cfg, s0+j) for j in range(8)]))
json.dump(truth_f, open("wb/first_truths.json","w"))
# full-population effect distribution: verify-reaching truths (all) + first-convicted truths
# (sampled, weight = N_first/60 each)
tv = [BM - e["true"] for e in all_ev if e["stage"]=="verify"]
tf = [BM - v for v in truth_f.values()]
w = [1.0]*len(tv) + [len(firsts)/len(tf)]*len(tf)
d_all = np.array(tv + tf); w = np.array(w); w = w/w.sum()
mc = np.random.default_rng(1)
num = den = 0
draws = mc.choice(len(d_all), 400_000, p=w)
for di in draws:
    d = d_all[di]
    l1 = -d + mc.normal(0, SIG)
    if l1 >= 0: continue
    m3 = (l1 + (-d+mc.normal(0,SIG)) + (-d+mc.normal(0,SIG)))/3
    if m3 >= 0:
        den += 1
        if d > 0: num += 1
print(f"de-conditioned matched theory W_B: {num/den:.3f}  (measured 9/26 = 0.346 [0.172,0.557])")
# W_A on the same full population for free
numA = denA = 0
for di in mc.choice(len(d_all), 400_000, p=w):
    d = d_all[di]
    if -d + mc.normal(0, SIG) >= 0:
        denA += 1
        if d > 0: numA += 1
print(f"de-conditioned matched theory W_A: {numA/denA:.3f}; measured first-test W_A from sample: {sum(1 for v in tf if v>0)}/{len(tf)} = {sum(1 for v in tf if v>0)/len(tf):.3f}")
