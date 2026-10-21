"""Verdict-pipeline replay on the FCNet tabular HPO benchmark (Klein & Hutter 2019).
Each of ~62k configs per task has 4 independent training runs -> verdict = run 0,
ground truth = mean of runs 1-3 (out-of-sample). Massive event counts, zero training.

Setup (needs ~2GB disk, internet):
  wget http://ml4aad.org/wp-content/uploads/2019/01/fcnet_tabular_benchmarks.tar.gz
  tar xzf fcnet_tabular_benchmarks.tar.gz
  pip install h5py numpy
  python fcnet_replay.py fcnet_tabular_benchmarks/fcnet_slice_localization_data.hdf5
Run it for all four .hdf5 tasks; redirect the printed blocks to a file if you want them saved.
"""
import sys, json, h5py, numpy as np

f = h5py.File(sys.argv[1], "r")
keys = list(f.keys())
rng = np.random.default_rng(0)
# sample configs to keep memory sane; raise for the full run
N = min(len(keys), int(sys.argv[2]) if len(sys.argv) > 2 else 20000)
sel = rng.choice(len(keys), N, replace=False)
V = np.array([f[keys[i]]["valid_mse"][:, -1] for i in sel])  # (N, 4) final val MSE, 4 seeds
f.close()
verdict = V[:, 0]
truth = V[:, 1:].mean(1)
truth_se = V[:, 1:].std(1, ddof=1) / np.sqrt(3)
# baseline = median config performance (a realistic incumbent); sigma = within-config seed std
base = np.median(truth)
sigma = float(np.median(V.std(1, ddof=1)))
eff = base - truth            # >0 = genuinely better than incumbent
obs = base - verdict
convicted = obs <= 0
wrongA = convicted & (eff > 0)
from math import erf
ndtr = lambda z: 0.5 * (1 + np.vectorize(erf)(z / np.sqrt(2)))
aware = ndtr(eff[convicted] / np.maximum(truth_se[convicted], 1e-12)).mean()
print(f"TASK {sys.argv[1]}")
print(f"configs {N}, sigma(run) {sigma:.5f}, convicted {convicted.sum()}")
print(f"W_A point {wrongA.sum()/convicted.sum():.4f}  measurement-aware {aware:.4f}")
q = np.quantile(np.abs(eff[wrongA]) / sigma, [0.25, 0.5, 0.75]) if wrongA.sum() else [0,0,0]
print(f"wrongful effect sizes (sigma units) quartiles: {np.round(q,3)}")
# marginal-concentration check: P(convict | effect bucket)
for lo, hi in [(0,0.25),(0.25,0.5),(0.5,1),(1,2),(2,100)]:
    m = (eff/sigma > lo) & (eff/sigma <= hi)
    if m.sum() > 20:
        print(f"  P(convicted | true effect in ({lo},{hi}] sigma) = {convicted[m].mean():.3f}  (n={m.sum()})")
print(json.dumps({"task": sys.argv[1], "N": int(N), "sigma": sigma,
                  "convicted": int(convicted.sum()), "wrongful": int(wrongA.sum()),
                  "W_A": float(wrongA.sum()/convicted.sum()), "W_A_aware": float(aware)}))
